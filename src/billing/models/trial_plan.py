"""dtcoder 9.9 尝鲜价套餐 — 套餐与 SKU 配置数据模型（Task 1）。

本模块刻意不依赖任何具体 ORM（SQLAlchemy / Django ORM 等），以纯 dataclass +
可注入的内存仓储实现，保证单测可独立运行、无外部依赖。
后续接入真实 ORM 时，只需将 ``TrialPlanRepo`` 替换为 ORM 实现并复用同一组
dataclass / 迁移函数即可。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


class DuplicatePlanError(Exception):
    """plan_code 唯一约束冲突：已存在同 plan_code 的 active 套餐。"""


class PlanNotFoundError(KeyError):
    """未找到指定 plan_code 的 active 套餐。"""


# ---------------------------------------------------------------------------
# SSOT: dtcoder 9.9 尝鲜价套餐默认配置
# ---------------------------------------------------------------------------

TRIAL_PLAN_CODE = "trial-9.9-monthly"

DEFAULT_TRIAL_ENTITLEMENTS: dict = {
    "monthly_token_limit": 2000000,
    "max_concurrent_sessions": 3,
    "context_window": 131072,
    "model_tier": ["base", "flagship"],
    "flagship_rate_limit_per_hour": 20,
    "advanced_skills": True,
    "priority_support": True,
    "history_retention_days": 90,
}

# quota_limits 与 entitlements 区分：entitlements 描述“有哪些权益”，
# quota_limits 描述“各权益的硬上限 / 风控阈值”，便于 Task 2/4 直接消费。
DEFAULT_TRIAL_QUOTA_LIMITS: dict = {
    "monthly_token_limit": 2000000,
    "max_concurrent_sessions": 3,
    "flagship_rate_limit_per_hour": 20,
    "history_retention_days": 90,
    "purchase_limit_per_user": 1,
}

DEFAULT_TRIAL_PLAN = {
    "plan_code": TRIAL_PLAN_CODE,
    "name": "dtcoder 尝鲜版（首月）",
    "price": Decimal("9.90"),
    "duration_days": 30,
    "entitlements": DEFAULT_TRIAL_ENTITLEMENTS,
    "quota_limits": DEFAULT_TRIAL_QUOTA_LIMITS,
    "purchase_limit": 1,
    "is_active": True,
}


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class TrialPlan:
    """尝鲜价套餐定义。

    字段约束（构造时校验）：
      - plan_code: 非空，唯一
      - price: Decimal > 0
      - duration_days: int > 0
      - purchase_limit: int >= 1（默认 1，每自然用户限购 1 单）
      - is_active: bool，默认 True
    """

    plan_code: str
    price: Decimal
    duration_days: int
    entitlements: dict = field(default_factory=dict)
    quota_limits: dict = field(default_factory=dict)
    name: str = ""
    purchase_limit: int = 1
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.plan_code or not isinstance(self.plan_code, str):
            raise ValueError("plan_code 必须为非空字符串")
        # 统一用 Decimal 防止 float 精度漂移
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if not (self.price > 0):
            raise ValueError(f"price 必须 > 0，得到 {self.price}")
        if not isinstance(self.duration_days, int) or isinstance(self.duration_days, bool):
            raise TypeError("duration_days 必须为 int")
        if self.duration_days <= 0:
            raise ValueError(f"duration_days 必须 > 0，得到 {self.duration_days}")
        if not isinstance(self.purchase_limit, int) or isinstance(self.purchase_limit, bool):
            raise TypeError("purchase_limit 必须为 int")
        if self.purchase_limit < 1:
            raise ValueError(f"purchase_limit 必须 >= 1，得到 {self.purchase_limit}")
        if not isinstance(self.is_active, bool):
            raise TypeError("is_active 必须为 bool")
        if self.entitlements is None:
            self.entitlements = {}
        if self.quota_limits is None:
            self.quota_limits = {}


@dataclass
class TrialPurchaseRecord:
    """尝鲜价套餐购买记录（限购风控三重去重维度载体，Task 2 校验消费）。"""

    user_id: str
    device_fingerprint: str
    payment_method_hash: str
    purchased_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "paid"  # paid / refunded / pending

    def __post_init__(self) -> None:
        if not self.user_id or not isinstance(self.user_id, str):
            raise ValueError("user_id 必须为非空字符串")
        if not self.device_fingerprint or not isinstance(self.device_fingerprint, str):
            raise ValueError("device_fingerprint 必须为非空字符串")
        if not self.payment_method_hash or not isinstance(self.payment_method_hash, str):
            raise ValueError("payment_method_hash 必须为非空字符串")
        if not isinstance(self.purchased_at, datetime):
            raise TypeError("purchased_at 必须为 datetime")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("status 必须为非空字符串")


# ---------------------------------------------------------------------------
# 可注入的内存仓储（纯 dict 存储 + 线程安全锁，便于单测与未来替换为 ORM）
# ---------------------------------------------------------------------------


class TrialPlanRepo:
    """内存仓储：按 plan_code 唯一索引 active 套餐。

    仓储为可注入对象（依赖注入），测试可构造独立实例互不干扰。
    """

    def __init__(self) -> None:
        self._plans: dict[str, TrialPlan] = {}
        self._lock = threading.RLock()

    def add(self, plan: TrialPlan) -> TrialPlan:
        with self._lock:
            existing = self._plans.get(plan.plan_code)
            if existing is not None and existing.is_active:
                raise DuplicatePlanError(plan.plan_code)
            self._plans[plan.plan_code] = plan
            return plan

    def get(self, plan_code: str) -> Optional[TrialPlan]:
        with self._lock:
            plan = self._plans.get(plan_code)
            if plan is None or not plan.is_active:
                return None
            return plan

    def has(self, plan_code: str) -> bool:
        return self.get(plan_code) is not None

    def all(self) -> list[TrialPlan]:
        with self._lock:
            return [p for p in self._plans.values() if p.is_active]

    def clear(self) -> None:
        with self._lock:
            self._plans.clear()


# 进程级默认仓储：供 get_plan(plan_code) 便捷函数与迁移函数使用。
# 业务侧可通过依赖注入替换为 ORM 仓储，保持接口一致。
_default_repo: TrialPlanRepo = TrialPlanRepo()


def get_default_repo() -> TrialPlanRepo:
    """返回进程级默认仓储（便于依赖注入测试时观察 / 重置）。"""
    return _default_repo


def get_plan(plan_code: str, repo: Optional[TrialPlanRepo] = None) -> Optional[TrialPlan]:
    """查询 active 套餐。未找到返回 None（不抛异常，便于调用方做空值分支）。"""
    repo = repo if repo is not None else _default_repo
    return repo.get(plan_code)


def require_plan(plan_code: str, repo: Optional[TrialPlanRepo] = None) -> TrialPlan:
    """查询 active 套餐，未找到抛 PlanNotFoundError。"""
    plan = get_plan(plan_code, repo=repo)
    if plan is None:
        raise PlanNotFoundError(plan_code)
    return plan


# ---------------------------------------------------------------------------
# 迁移函数（idempotent）：插入 trial-9.9-monthly 默认配置
# ---------------------------------------------------------------------------


def add_trial_plan_migration(repo: Optional[TrialPlanRepo] = None) -> TrialPlan:
    """幂等插入 ``trial-9.9-monthly`` 默认套餐配置。

    - 已存在 active 套餐时直接返回现有实例（不抛错、不覆盖），保证迁移可重复执行。
    - 新仓储或被清空后执行迁移可重新写入默认配置。
    """
    repo = repo if repo is not None else _default_repo
    existing = repo.get(TRIAL_PLAN_CODE)
    if existing is not None:
        return existing
    plan = TrialPlan(
        plan_code=DEFAULT_TRIAL_PLAN["plan_code"],
        name=DEFAULT_TRIAL_PLAN["name"],
        price=DEFAULT_TRIAL_PLAN["price"],
        duration_days=DEFAULT_TRIAL_PLAN["duration_days"],
        entitlements=dict(DEFAULT_TRIAL_PLAN["entitlements"]),
        quota_limits=dict(DEFAULT_TRIAL_PLAN["quota_limits"]),
        purchase_limit=DEFAULT_TRIAL_PLAN["purchase_limit"],
        is_active=DEFAULT_TRIAL_PLAN["is_active"],
    )
    return repo.add(plan)


__all__ = [
    "TRIAL_PLAN_CODE",
    "DEFAULT_TRIAL_ENTITLEMENTS",
    "DEFAULT_TRIAL_QUOTA_LIMITS",
    "DEFAULT_TRIAL_PLAN",
    "TrialPlan",
    "TrialPurchaseRecord",
    "TrialPlanRepo",
    "DuplicatePlanError",
    "PlanNotFoundError",
    "get_default_repo",
    "get_plan",
    "require_plan",
    "add_trial_plan_migration",
]
