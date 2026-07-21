"""Quota enforcement layer.

``QuotaLimiter`` wraps the three runtime checks required by Task 4:

  * ``check_token(user, plan_code, tokens)``     -> monthly token cap (429 on breach)
  * ``check_concurrency(user, plan_code, current)`` -> max concurrent sessions
  * ``check_flagship_rate(user, plan_code)``       -> flagship calls/hour cap

Per-plan thresholds come from :func:`entitlement.resolver.resolve_entitlements`.
The counter storage is injectable so tests (and future persistence backends)
can substitute an in-memory implementation. A default in-memory repo is used
when none is supplied.

Design note on signatures: the SSOT brief writes ``check_concurrency(user,
current)`` / ``check_flagship_rate(user)`` as shorthand, but the per-plan
threshold is required to evaluate the limit, so all three methods take an
explicit ``plan_code`` argument. This keeps the limiter stateless w.r.t. the
caller's subscription and lets free/basic-99/trial behaviour be asserted in
the same regression suite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from entitlement.resolver import Entitlements, resolve_entitlements


# --- decision result ------------------------------------------------------

@dataclass(frozen=True)
class QuotaDecision:
    """Outcome of a quota check.

    ``status_code`` mirrors an HTTP-style code: ``0`` when allowed, ``429``
    when rate-limited / over quota, ``403`` when the requested tier is not
    available at all for the plan.
    """

    allowed: bool
    status_code: int = 0
    reason: str = ""
    plan_code: str = ""

    def __bool__(self) -> bool:  # convenience: ``if limiter.check_token(...)``
        return self.allowed


# --- injectable counter storage ------------------------------------------

@runtime_checkable
class CounterRepo(Protocol):
    """Minimal counter storage interface used by :class:`QuotaLimiter`."""

    def get_monthly_token_usage(self, user: str) -> int: ...

    def incr_monthly_token_usage(self, user: str, tokens: int) -> int: ...

    def get_flagship_calls(self, user: str) -> int: ...

    def incr_flagship_calls(self, user: str) -> int: ...


class InMemoryCounterRepo:
    """Default in-memory counter repo (suitable for tests and dev runs)."""

    def __init__(self) -> None:
        self._monthly_tokens: dict[str, int] = {}
        self._flagship_calls: dict[str, int] = {}

    def get_monthly_token_usage(self, user: str) -> int:
        return self._monthly_tokens.get(user, 0)

    def incr_monthly_token_usage(self, user: str, tokens: int) -> int:
        new_val = self._monthly_tokens.get(user, 0) + int(tokens)
        self._monthly_tokens[user] = new_val
        return new_val

    def get_flagship_calls(self, user: str) -> int:
        return self._flagship_calls.get(user, 0)

    def incr_flagship_calls(self, user: str) -> int:
        new_val = self._flagship_calls.get(user, 0) + 1
        self._flagship_calls[user] = new_val
        return new_val

    def reset(self, user: Optional[str] = None) -> None:
        """Reset counters for a user (or all users when ``user`` is None)."""
        if user is None:
            self._monthly_tokens.clear()
            self._flagship_calls.clear()
        else:
            self._monthly_tokens.pop(user, None)
            self._flagship_calls.pop(user, None)


# --- limiter --------------------------------------------------------------

class QuotaLimiter:
    """Plan-aware quota limiter.

    Parameters
    ----------
    counter_repo:
        Optional :class:`CounterRepo` implementation. Defaults to a fresh
        :class:`InMemoryCounterRepo`.
    """

    def __init__(self, counter_repo: Optional[CounterRepo] = None) -> None:
        self.repo: CounterRepo = counter_repo if counter_repo is not None else InMemoryCounterRepo()

    # -- token cap ---------------------------------------------------------

    def check_token(self, user: str, plan_code: str, tokens: int) -> QuotaDecision:
        """Return 429 when adding ``tokens`` would exceed the monthly cap.

        For ``basic-99`` (``monthly_token_limit is None``) the check is a
        no-op and the counter is not incremented (unlimited plan).
        """
        ents = resolve_entitlements(plan_code)
        limit = ents.monthly_token_limit
        if limit is None:
            # unlimited plan: still record usage for observability but never block
            self.repo.incr_monthly_token_usage(user, tokens)
            return QuotaDecision(allowed=True, status_code=0, reason="unlimited", plan_code=plan_code)
        usage = self.repo.get_monthly_token_usage(user)
        if usage + int(tokens) > limit:
            return QuotaDecision(
                allowed=False,
                status_code=429,
                reason="monthly_token_limit_exceeded",
                plan_code=plan_code,
            )
        self.repo.incr_monthly_token_usage(user, tokens)
        return QuotaDecision(allowed=True, status_code=0, reason="ok", plan_code=plan_code)

    # -- concurrency -------------------------------------------------------

    def check_concurrency(
        self, user: str, plan_code: str, current_sessions: int
    ) -> QuotaDecision:
        """Reject when ``current_sessions`` exceeds the plan's session cap.

        ``current_sessions`` is the count *including* the session that is
        being admitted right now, so for trial (cap=3) the 4th session is
        rejected (status 429).
        """
        ents = resolve_entitlements(plan_code)
        cap = ents.max_concurrent_sessions
        if int(current_sessions) > cap:
            return QuotaDecision(
                allowed=False,
                status_code=429,
                reason="max_concurrent_sessions_exceeded",
                plan_code=plan_code,
            )
        return QuotaDecision(allowed=True, status_code=0, reason="ok", plan_code=plan_code)

    # -- flagship rate -----------------------------------------------------

    def check_flagship_rate(self, user: str, plan_code: str) -> QuotaDecision:
        """Enforce the per-hour flagship call cap.

        * If the plan has no flagship tier (e.g. ``free``) -> 403
          (``flagship_not_available``).
        * If the plan has unlimited flagship calls (``basic-99``) -> allow.
        * Otherwise (``trial-9.9-monthly``) the 21st call in the hour is
          rejected with 429.
        """
        ents: Entitlements = resolve_entitlements(plan_code)
        if "flagship" not in ents.model_tier:
            return QuotaDecision(
                allowed=False,
                status_code=403,
                reason="flagship_not_available",
                plan_code=plan_code,
            )
        cap = ents.flagship_rate_limit_per_hour
        if cap is None:
            return QuotaDecision(allowed=True, status_code=0, reason="unlimited", plan_code=plan_code)
        current = self.repo.get_flagship_calls(user)
        if current >= cap:
            return QuotaDecision(
                allowed=False,
                status_code=429,
                reason="flagship_rate_limit_exceeded",
                plan_code=plan_code,
            )
        self.repo.incr_flagship_calls(user)
        return QuotaDecision(allowed=True, status_code=0, reason="ok", plan_code=plan_code)
