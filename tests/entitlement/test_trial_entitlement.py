"""TDD suite for Task 4: entitlement resolver + quota limiter.

Covers (per DoD):
  * trial-9.9-monthly entitlements match the SSOT matrix exactly.
  * UnknownPlan raised for unknown plan_code.
  * free / basic-99 placeholders resolve to SSOT 对照 values.
  * Trial user over the 2,000,000 monthly token cap -> 429.
  * Trial 4th concurrent session rejected (3rd allowed).
  * Trial flagship rate: 21st call/hour rejected with 429 (20 allowed).
  * Free user: token cap at 500,000 (not 2,000,000), concurrency cap at 1,
    flagship unavailable.
  * basic-99 user: unlimited tokens (large batch allowed), 5 concurrent ok /
    6 rejected, flagship unlimited.
  * Counter storage is injectable (custom repo stub).

These tests are written with plain ``assert`` so they run under both
``pytest`` and a bare ``python`` invocation (see the ``__main__`` runner
at the bottom).
"""

from __future__ import annotations

import os
import sys

# Make ``src/`` importable without an installed package (namespace packages).
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from entitlement.resolver import (  # noqa: E402
    Entitlements,
    UnknownPlan,
    registered_plan_codes,
    resolve_entitlements,
)
from quota.limiter import InMemoryCounterRepo, QuotaDecision, QuotaLimiter  # noqa: E402


TRIAL = "trial-9.9-monthly"
FREE = "free"
BASIC = "basic-99"


# --- resolver -------------------------------------------------------------

def test_trial_entitlements_match_ssot():
    e = resolve_entitlements(TRIAL)
    assert isinstance(e, Entitlements)
    assert e.monthly_token_limit == 2_000_000
    assert e.max_concurrent_sessions == 3
    assert e.context_window == 131_072
    assert e.model_tier == ["base", "flagship"]
    assert e.flagship_rate_limit_per_hour == 20
    assert e.advanced_skills is True
    assert e.priority_support is True
    assert e.history_retention_days == 90
    # dict form mirrors the SSOT JSON matrix
    assert e.to_dict() == {
        "monthly_token_limit": 2_000_000,
        "max_concurrent_sessions": 3,
        "context_window": 131_072,
        "model_tier": ["base", "flagship"],
        "flagship_rate_limit_per_hour": 20,
        "advanced_skills": True,
        "priority_support": True,
        "history_retention_days": 90,
    }


def test_free_placeholder_matches_ssot_contrast():
    e = resolve_entitlements(FREE)
    assert e.monthly_token_limit == 500_000
    assert e.max_concurrent_sessions == 1
    assert e.context_window == 32_768
    assert e.model_tier == ["base"]
    assert e.advanced_skills is False
    assert e.priority_support is False
    assert e.history_retention_days == 7


def test_basic_99_placeholder_matches_ssot_contrast():
    e = resolve_entitlements(BASIC)
    assert e.monthly_token_limit is None  # unlimited
    assert e.max_concurrent_sessions == 5
    assert e.context_window == 200_000
    assert e.model_tier == ["base", "flagship"]  # 全模型
    assert e.flagship_rate_limit_per_hour is None  # unlimited
    assert e.history_retention_days is None  # unlimited


def test_unknown_plan_raises():
    for bad in ("trial-9.9", "trial", "", "premium", None):
        try:
            resolve_entitlements(bad)  # type: ignore[arg-type]
        except UnknownPlan:
            continue
        raise AssertionError(f"expected UnknownPlan for {bad!r}")


def test_registered_plan_codes_include_all_three():
    codes = registered_plan_codes()
    assert {TRIAL, FREE, BASIC}.issubset(set(codes))


# --- limiter: trial token cap -------------------------------------------

def test_trial_token_within_limit_allowed():
    limiter = QuotaLimiter()
    d = limiter.check_token("u1", TRIAL, 1_000_000)
    assert d.allowed and d.status_code == 0


def test_trial_token_over_limit_returns_429():
    """TDD core: 尝鲜用户超 token 上限 -> 429."""
    limiter = QuotaLimiter()
    # consume up to the cap exactly (allowed), then 1 more token -> 429
    ok = limiter.check_token("u1", TRIAL, 2_000_000)
    assert ok.allowed, "consuming exactly the cap should be allowed"
    over = limiter.check_token("u1", TRIAL, 1)
    assert over.allowed is False
    assert over.status_code == 429
    assert over.reason == "monthly_token_limit_exceeded"


def test_trial_token_crosses_boundary():
    limiter = QuotaLimiter()
    # 1_999_999 + 2 = 2_000_001 > 2_000_000 -> reject
    assert limiter.check_token("u1", TRIAL, 1_999_999).allowed
    d = limiter.check_token("u1", TRIAL, 2)
    assert d.status_code == 429 and d.allowed is False


# --- limiter: trial concurrency ------------------------------------------

def test_trial_concurrency_3_allowed_4th_rejected():
    """TDD core: 第 4 个并发被拒."""
    limiter = QuotaLimiter()
    for n in (1, 2, 3):
        d = limiter.check_concurrency("u1", TRIAL, n)
        assert d.allowed, f"session #{n} should be allowed for trial"
    d4 = limiter.check_concurrency("u1", TRIAL, 4)
    assert d4.allowed is False
    assert d4.status_code == 429
    assert d4.reason == "max_concurrent_sessions_exceeded"


# --- limiter: trial flagship rate ----------------------------------------

def test_trial_flagship_rate_20_allowed_21st_limited():
    """TDD core: 旗舰超速被限 (cap 20/h)."""
    limiter = QuotaLimiter()
    for _ in range(20):
        d = limiter.check_flagship_rate("u1", TRIAL)
        assert d.allowed, "first 20 flagship calls must be allowed"
    d21 = limiter.check_flagship_rate("u1", TRIAL)
    assert d21.allowed is False
    assert d21.status_code == 429
    assert d21.reason == "flagship_rate_limit_exceeded"


# --- regression: free user behaviour -------------------------------------

def test_free_token_cap_is_500000_not_2million():
    """免费版 token 超 50 万才限（不是 200 万）."""
    limiter = QuotaLimiter()
    assert limiter.check_token("u1", FREE, 500_000).allowed
    over = limiter.check_token("u1", FREE, 1)
    assert over.status_code == 429 and over.allowed is False


def test_free_concurrency_cap_is_1():
    """免费版并发超 1 才限."""
    limiter = QuotaLimiter()
    assert limiter.check_concurrency("u1", FREE, 1).allowed
    d2 = limiter.check_concurrency("u1", FREE, 2)
    assert d2.allowed is False and d2.status_code == 429


def test_free_flagship_unavailable():
    """免费版无旗舰档 -> 403 (not a 429 rate limit)."""
    limiter = QuotaLimiter()
    d = limiter.check_flagship_rate("u1", FREE)
    assert d.allowed is False
    assert d.status_code == 403
    assert d.reason == "flagship_not_available"


# --- regression: basic-99 user behaviour ----------------------------------

def test_basic_99_token_unlimited():
    """正价基础版无限 token."""
    limiter = QuotaLimiter()
    # a batch far beyond the trial cap must be allowed
    d = limiter.check_token("u1", BASIC, 10_000_000)
    assert d.allowed and d.status_code == 0
    # subsequent large batch still allowed
    assert limiter.check_token("u1", BASIC, 10_000_000).allowed


def test_basic_99_concurrency_cap_is_5():
    """正价基础版并发 5 ok / 6 拒."""
    limiter = QuotaLimiter()
    for n in (1, 2, 3, 4, 5):
        assert limiter.check_concurrency("u1", BASIC, n).allowed, f"session #{n} allowed"
    d6 = limiter.check_concurrency("u1", BASIC, 6)
    assert d6.allowed is False and d6.status_code == 429


def test_basic_99_flagship_unlimited():
    """正价基础版旗舰无限速."""
    limiter = QuotaLimiter()
    for _ in range(50):
        d = limiter.check_flagship_rate("u1", BASIC)
        assert d.allowed, "basic-99 flagship must be unlimited"


# --- injectable counter storage ------------------------------------------

def test_counter_repo_is_injectable():
    """Custom repo stub steers limiter decisions (dependency injection)."""

    class StubRepo:
        def __init__(self, tokens=0, calls=0):
            self._t = tokens
            self._c = calls

        def get_monthly_token_usage(self, user):
            return self._t

        def incr_monthly_token_usage(self, user, tokens):
            self._t += tokens
            return self._t

        def get_flagship_calls(self, user):
            return self._c

        def incr_flagship_calls(self, user):
            self._c += 1
            return self._c

    # pre-fill usage to exactly the trial cap -> next 1 token rejected
    limiter = QuotaLimiter(counter_repo=StubRepo(tokens=2_000_000))
    d = limiter.check_token("u1", TRIAL, 1)
    assert d.status_code == 429 and d.allowed is False

    # pre-fill flagship calls to cap -> next call rejected
    limiter2 = QuotaLimiter(counter_repo=StubRepo(calls=20))
    d2 = limiter2.check_flagship_rate("u1", TRIAL)
    assert d2.status_code == 429 and d2.allowed is False

    # InMemoryCounterRepo implements the protocol
    assert isinstance(InMemoryCounterRepo(), object)


def test_users_are_isolated_in_default_repo():
    """Counters must be keyed per user."""
    limiter = QuotaLimiter()
    # u1 hits the trial cap
    assert limiter.check_token("u1", TRIAL, 2_000_000).allowed
    assert limiter.check_token("u1", TRIAL, 1).status_code == 429
    # u2 is independent and still has the full cap
    d = limiter.check_token("u2", TRIAL, 2_000_000)
    assert d.allowed and d.status_code == 0


# --- decision bool convenience -------------------------------------------

def test_decision_truthiness():
    assert bool(QuotaDecision(allowed=True, status_code=0))
    assert not bool(QuotaDecision(allowed=False, status_code=429))


# --- minimal runner so the file is runnable without pytest ----------------

def _collect_tests():
    return [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]


if __name__ == "__main__":
    failed = 0
    passed = 0
    for name, fn in _collect_tests():
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"PASS {name}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if failed == 0 else 1)
