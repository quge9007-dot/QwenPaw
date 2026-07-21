"""Entitlement resolver for dtcoder plans.

Maps a ``plan_code`` to its SSOT entitlements structure. The values for
``trial-9.9-monthly`` mirror the authoritative entitlements matrix in
``local-docs/dtcoder-9.9-trial-tasks.md`` (## SSOT 合约 -> 权益矩阵):

    {
      "monthly_token_limit": 2000000,
      "max_concurrent_sessions": 3,
      "context_window": 131072,
      "model_tier": ["base", "flagship"],
      "flagship_rate_limit_per_hour": 20,
      "advanced_skills": true,
      "priority_support": true,
      "history_retention_days": 90
    }

Placeholder plans (per SSOT 对照):
  * ``free``     : 500_000 tokens / 1 concurrent / 32K ctx / base-only / 7d history.
  * ``basic-99`` : unlimited tokens / 5 concurrent / 200K ctx / all models / unlimited history.

This module is intentionally dependency-free (pure dataclasses + a static
registry) so it can be unit-tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class UnknownPlan(ValueError):
    """Raised when ``plan_code`` is not a recognised plan."""


@dataclass(frozen=True)
class Entitlements:
    """Structured entitlements for a plan.

    A ``None`` value for a limit field means "unlimited" (used by the
    ``basic-99`` placeholder for token / flagship-rate / history).
    """

    plan_code: str
    monthly_token_limit: Optional[int]
    max_concurrent_sessions: int
    context_window: int
    model_tier: List[str] = field(default_factory=list)
    flagship_rate_limit_per_hour: Optional[int] = None
    advanced_skills: bool = False
    priority_support: bool = False
    history_retention_days: Optional[int] = None

    def to_dict(self) -> dict:
        """Return the SSOT-shaped entitlements dict (matches the JSON matrix)."""
        return {
            "monthly_token_limit": self.monthly_token_limit,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "context_window": self.context_window,
            "model_tier": list(self.model_tier),
            "flagship_rate_limit_per_hour": self.flagship_rate_limit_per_hour,
            "advanced_skills": self.advanced_skills,
            "priority_support": self.priority_support,
            "history_retention_days": self.history_retention_days,
        }


# --- SSOT plan registry ---------------------------------------------------

_TRIAL_9_9 = Entitlements(
    plan_code="trial-9.9-monthly",
    monthly_token_limit=2_000_000,
    max_concurrent_sessions=3,
    context_window=131_072,
    model_tier=["base", "flagship"],
    flagship_rate_limit_per_hour=20,
    advanced_skills=True,
    priority_support=True,
    history_retention_days=90,
)

_FREE = Entitlements(
    plan_code="free",
    monthly_token_limit=500_000,
    max_concurrent_sessions=1,
    context_window=32_768,
    model_tier=["base"],
    flagship_rate_limit_per_hour=0,  # flagship tier not available
    advanced_skills=False,
    priority_support=False,
    history_retention_days=7,
)

_BASIC_99 = Entitlements(
    plan_code="basic-99",
    monthly_token_limit=None,  # unlimited
    max_concurrent_sessions=5,
    context_window=200_000,
    model_tier=["base", "flagship"],  # 全模型
    flagship_rate_limit_per_hour=None,  # unlimited
    advanced_skills=True,
    priority_support=True,
    history_retention_days=None,  # unlimited
)

_REGISTRY = {
    _TRIAL_9_9.plan_code: _TRIAL_9_9,
    _FREE.plan_code: _FREE,
    _BASIC_99.plan_code: _BASIC_99,
}


def resolve_entitlements(plan_code: str) -> Entitlements:
    """Return the :class:`Entitlements` for ``plan_code``.

    Raises:
        UnknownPlan: if ``plan_code`` is not a registered plan.
    """
    if not isinstance(plan_code, str):
        raise UnknownPlan(f"plan_code must be a string, got {type(plan_code).__name__}")
    try:
        return _REGISTRY[plan_code]
    except KeyError:
        raise UnknownPlan(f"Unknown plan_code: {plan_code!r}")


def registered_plan_codes() -> List[str]:
    """Return the list of currently registered plan codes (test helper)."""
    return list(_REGISTRY.keys())
