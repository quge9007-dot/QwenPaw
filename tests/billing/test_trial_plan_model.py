"""Task 1 TDD：dtcoder 9.9 尝鲜价套餐数据模型单测。

覆盖 DoD：限购=1、price>0、duration_days>0、get_plan('trial-9.9-monthly')
返回正确套餐、重复 plan_code 唯一约束、迁移幂等。

无外部依赖：纯 dataclass + 内存仓储，使用独立 repo 实例避免进程级状态串扰。
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from decimal import Decimal

import pytest

# 让测试在未安装为 package 时也能直接定位 src/ 下的 billing 模块。
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from billing.models.trial_plan import (  # noqa: E402
    DEFAULT_TRIAL_ENTITLEMENTS,
    DEFAULT_TRIAL_QUOTA_LIMITS,
    TRIAL_PLAN_CODE,
    DuplicatePlanError,
    PlanNotFoundError,
    TrialPlan,
    TrialPlanRepo,
    TrialPurchaseRecord,
    add_trial_plan_migration,
    get_plan,
    require_plan,
)


# ---------------------------------------------------------------------------
# 基础校验：price>0 / duration_days>0 / purchase_limit>=1
# ---------------------------------------------------------------------------


class TestTrialPlanValidation:
    def test_price_must_be_positive(self):
        with pytest.raises(ValueError):
            TrialPlan(plan_code="x", price=Decimal("0"), duration_days=30)
        with pytest.raises(ValueError):
            TrialPlan(plan_code="x", price=Decimal("-1"), duration_days=30)

    def test_duration_days_must_be_positive(self):
        with pytest.raises(ValueError):
            TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=0)
        with pytest.raises(ValueError):
            TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=-1)

    def test_duration_days_must_be_int_not_bool(self):
        with pytest.raises(TypeError):
            TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=True)  # type: ignore[arg-type]

    def test_purchase_limit_defaults_to_one(self):
        plan = TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=30)
        assert plan.purchase_limit == 1

    def test_purchase_limit_must_be_at_least_one(self):
        with pytest.raises(ValueError):
            TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=30, purchase_limit=0)

    def test_default_is_active_true(self):
        plan = TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=30)
        assert plan.is_active is True

    def test_entitlements_default_empty_dict(self):
        plan = TrialPlan(plan_code="x", price=Decimal("9.90"), duration_days=30)
        assert plan.entitlements == {}
        assert plan.quota_limits == {}


# ---------------------------------------------------------------------------
# 默认配置 / SSOT 一致性
# ---------------------------------------------------------------------------


class TestDefaultTrialPlanConfig:
    def test_default_entitlements_match_ssot(self):
        assert DEFAULT_TRIAL_ENTITLEMENTS == {
            "monthly_token_limit": 2000000,
            "max_concurrent_sessions": 3,
            "context_window": 131072,
            "model_tier": ["base", "flagship"],
            "flagship_rate_limit_per_hour": 20,
            "advanced_skills": True,
            "priority_support": True,
            "history_retention_days": 90,
        }

    def test_default_plan_fields(self):
        plan = TrialPlan(
            plan_code=TRIAL_PLAN_CODE,
            price=Decimal("9.90"),
            duration_days=30,
            entitlements=DEFAULT_TRIAL_ENTITLEMENTS,
            quota_limits=DEFAULT_TRIAL_QUOTA_LIMITS,
        )
        assert plan.plan_code == "trial-9.9-monthly"
        assert plan.price == Decimal("9.90")
        assert plan.duration_days == 30
        assert plan.purchase_limit == 1
        assert plan.is_active is True


# ---------------------------------------------------------------------------
# get_plan 查询
# ---------------------------------------------------------------------------


class TestGetPlan:
    def test_get_plan_returns_none_for_unknown(self):
        repo = TrialPlanRepo()
        assert get_plan("trial-9.9-monthly", repo=repo) is None

    def test_get_plan_returns_active_plan_after_migration(self):
        repo = TrialPlanRepo()
        add_trial_plan_migration(repo=repo)
        plan = get_plan("trial-9.9-monthly", repo=repo)
        assert plan is not None
        assert plan.plan_code == "trial-9.9-monthly"
        assert plan.price == Decimal("9.90")
        assert plan.duration_days == 30
        assert plan.entitlements["monthly_token_limit"] == 2000000
        assert plan.quota_limits["purchase_limit_per_user"] == 1

    def test_require_plan_raises_when_missing(self):
        repo = TrialPlanRepo()
        with pytest.raises(PlanNotFoundError):
            require_plan("trial-9.9-monthly", repo=repo)

    def test_get_plan_ignores_inactive(self):
        repo = TrialPlanRepo()
        plan = TrialPlan(
            plan_code="inactive-plan",
            price=Decimal("9.90"),
            duration_days=30,
            is_active=False,
        )
        repo.add(plan)
        assert get_plan("inactive-plan", repo=repo) is None


# ---------------------------------------------------------------------------
# 唯一约束：重复 plan_code
# ---------------------------------------------------------------------------


class TestUniquePlanCode:
    def test_duplicate_active_plan_code_raises(self):
        repo = TrialPlanRepo()
        repo.add(TrialPlan(plan_code="dup", price=Decimal("9.90"), duration_days=30))
        with pytest.raises(DuplicatePlanError):
            repo.add(TrialPlan(plan_code="dup", price=Decimal("9.90"), duration_days=30))

    def test_repos_are_isolated(self):
        """可注入仓储：两个独立 repo 不共享状态。"""
        a = TrialPlanRepo()
        b = TrialPlanRepo()
        a.add(TrialPlan(plan_code="iso", price=Decimal("9.90"), duration_days=30))
        assert b.get("iso") is None


# ---------------------------------------------------------------------------
# 迁移幂等
# ---------------------------------------------------------------------------


class TestMigrationIdempotent:
    def test_migration_inserts_plan_once(self):
        repo = TrialPlanRepo()
        first = add_trial_plan_migration(repo=repo)
        assert first.plan_code == TRIAL_PLAN_CODE
        assert len(repo.all()) == 1

    def test_migration_is_idempotent(self):
        repo = TrialPlanRepo()
        first = add_trial_plan_migration(repo=repo)
        second = add_trial_plan_migration(repo=repo)
        assert first is second
        assert len(repo.all()) == 1

    def test_migration_does_not_overwrite_existing(self):
        repo = TrialPlanRepo()
        # 预置一个被改动的 active 套餐，迁移不应覆盖它
        custom = TrialPlan(
            plan_code=TRIAL_PLAN_CODE,
            price=Decimal("19.90"),
            duration_days=60,
            purchase_limit=1,
        )
        repo.add(custom)
        returned = add_trial_plan_migration(repo=repo)
        assert returned is custom
        assert returned.price == Decimal("19.90")
        assert returned.duration_days == 60
        assert len(repo.all()) == 1

    def test_migration_on_fresh_repo_seeds_default(self):
        repo = TrialPlanRepo()
        plan = add_trial_plan_migration(repo=repo)
        assert plan.price == Decimal("9.90")
        assert plan.duration_days == 30
        assert plan.purchase_limit == 1
        assert plan.entitlements == DEFAULT_TRIAL_ENTITLEMENTS


# ---------------------------------------------------------------------------
# TrialPurchaseRecord 基础结构（Task 2 校验消费，此处仅校验可构造）
# ---------------------------------------------------------------------------


class TestTrialPurchaseRecord:
    def test_construct_record(self):
        rec = TrialPurchaseRecord(
            user_id="u-1",
            device_fingerprint="fp-abc",
            payment_method_hash="pm-hash-1",
        )
        assert rec.user_id == "u-1"
        assert rec.status == "paid"
        assert isinstance(rec.purchased_at, datetime)

    def test_record_requires_non_empty_fields(self):
        with pytest.raises(ValueError):
            TrialPurchaseRecord(user_id="", device_fingerprint="fp", payment_method_hash="pm")
        with pytest.raises(ValueError):
            TrialPurchaseRecord(user_id="u", device_fingerprint="", payment_method_hash="pm")
        with pytest.raises(ValueError):
            TrialPurchaseRecord(user_id="u", device_fingerprint="fp", payment_method_hash="")
