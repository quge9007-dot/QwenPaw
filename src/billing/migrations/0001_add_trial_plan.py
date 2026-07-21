"""迁移 0001：插入 dtcoder 9.9 尝鲜价套餐默认配置。

迁移函数 ``add_trial_plan_migration`` 已实现为幂等，此处仅作薄封装，
便于后续接入迁移框架（如 Alembic）时作为 upgrade() 入口。
"""

from __future__ import annotations

from typing import Optional

from src.billing.models.trial_plan import (
    TRIAL_PLAN_CODE,
    TrialPlan,
    TrialPlanRepo,
    add_trial_plan_migration,
)


MIGRATION_ID = "0001_add_trial_plan"


def upgrade(repo: Optional[TrialPlanRepo] = None) -> TrialPlan:
    """执行迁移：幂等插入 trial-9.9-monthly 默认套餐。"""
    return add_trial_plan_migration(repo=repo)


def downgrade(repo: Optional[TrialPlanRepo] = None) -> None:
    """回滚：将 trial-9.9-monthly 标记为非 active（不物理删除，保留历史）。

    当前内存仓储语义下不主动清空，避免误删业务数据；
    真实 ORM 迁移时应在此处将 is_active 置 False。
    """
    return None


__all__ = ["MIGRATION_ID", "upgrade", "downgrade", "TRIAL_PLAN_CODE"]
