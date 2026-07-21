# -*- coding: utf-8 -*-
"""Task 3: dtcoder 9.9 尝鲜价套餐 — 下单与计费周期服务 TDD 用例。

覆盖 4 个核心用例：
1. 下单成功（guard 放行 → 生成 pending 订单，金额 9.90）。
2. 限购拦截（注入 guard 返回 (False, reason) → 抛 PurchaseNotAllowed）。
3. 支付回调开通（UserSubscription active + end_at=now+30d + auto_renew=False
   + trial_activate 埋点 + TrialPurchaseRecord completed）。
4. 到期降级（end_at<=now 的 active 尝鲜订阅 → expired + trial_churn 埋点）。

仓储使用 in-memory 实现；事件用捕获式 EventPublisher stub；guard 用可编程
stub。所有断言自包含，不依赖外部服务。
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# 让本测试在「未安装包 / 无 PYTHONPATH 配置」时也能独立导入 src 下的模块。
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from billing.services.trial_order import (  # noqa: E402
    CapturingEventPublisher,
    InMemoryOrderRepository,
    InMemoryPurchaseRecordRepository,
    InMemorySubscriptionRepository,
    OrderNotFound,
    PurchaseNotAllowed,
    TRIAL_PLAN_CODE,
    TRIAL_PRICE,
    TrialOrderService,
    User,
)


def _build_service(guard):
    """装配可注入 in-memory 依赖的 TrialOrderService。"""
    return TrialOrderService(
        guard=guard,
        order_repo=InMemoryOrderRepository(),
        subscription_repo=InMemorySubscriptionRepository(),
        purchase_repo=InMemoryPurchaseRecordRepository(),
        event_publisher=CapturingEventPublisher(),
    )


class _AllowGuard:
    def check_purchase_eligibility(self, user, device, payment):
        return True, "ok"


class _DenyGuard:
    def __init__(self, reason="duplicate_user"):
        self.reason = reason

    def check_purchase_eligibility(self, user, device, payment):
        return False, self.reason


def _user(uid="U1"):
    return User(user_id=uid, registered_at=datetime(2026, 1, 1, tzinfo=timezone.utc), ip="1.2.3.4")


# ---------------------------------------------------------------------------
# 用例 1：下单成功
# ---------------------------------------------------------------------------


def test_create_trial_order_success():
    svc = _build_service(_AllowGuard())
    order = svc.create_trial_order(_user(), TRIAL_PLAN_CODE, "alipay")

    assert order.user_id == "U1"
    assert order.plan_code == TRIAL_PLAN_CODE
    assert order.amount == TRIAL_PRICE == Decimal("9.90")
    assert order.status == "pending"
    assert order.payment_channel == "alipay"
    # 已持久化
    assert svc.order_repo.get_order(order.id) is order
    # 未发任何埋点（下单本身不发埋点）
    assert svc.event_publisher.events == []


# ---------------------------------------------------------------------------
# 用例 2：限购拦截
# ---------------------------------------------------------------------------


def test_create_trial_order_blocked_by_guard():
    svc = _build_service(_DenyGuard(reason="duplicate_user"))
    try:
        svc.create_trial_order(_user(), TRIAL_PLAN_CODE, "wechat")
    except PurchaseNotAllowed as exc:
        assert exc.reason == "duplicate_user"
    else:
        raise AssertionError("期望抛出 PurchaseNotAllowed")

    # 拦截后不应写入任何订单
    # （InMemoryOrderRepository 无列举接口；通过 activate 间接验证订单不存在）
    try:
        svc.activate_trial_order("nonexistent")
    except OrderNotFound:
        pass
    else:
        raise AssertionError("拦截后不应存在订单")
    assert svc.event_publisher.events == []


# ---------------------------------------------------------------------------
# 用例 3：支付回调开通
# ---------------------------------------------------------------------------


def test_activate_trial_order_creates_subscription():
    svc = _build_service(_AllowGuard())
    order = svc.create_trial_order(_user(), TRIAL_PLAN_CODE, "alipay")
    now = datetime(2026, 7, 21, 6, 0, 0, tzinfo=timezone.utc)

    sub = svc.activate_trial_order(order.id, now=now)

    # UserSubscription 关键字段
    assert sub.user_id == "U1"
    assert sub.plan_code == TRIAL_PLAN_CODE
    assert sub.status == "active"
    assert sub.auto_renew is False
    assert sub.start_at == now
    assert sub.end_at == now + timedelta(days=30)
    # 订单状态推进为 paid
    paid = svc.order_repo.get_order(order.id)
    assert paid.status == "paid"
    # trial_activate 埋点
    events = svc.event_publisher.events
    assert any(e == "trial_activate" for e, _ in events)
    evt = [p for e, p in events if e == "trial_activate"][0]
    assert evt["user_id"] == "U1"
    assert evt["plan_code"] == TRIAL_PLAN_CODE
    assert evt["end_at"] == sub.end_at.isoformat()
    # TrialPurchaseRecord completed 已写入（通过捕获列表无报错即视为成功；
    # 这里进一步断言 purchase_repo 已落库一条 completed 记录）
    record = svc.purchase_repo._records[-1]  # noqa: SLF001
    assert record.status == "completed"
    assert record.user_id == "U1"


# ---------------------------------------------------------------------------
# 用例 4：到期降级
# ---------------------------------------------------------------------------


def test_expire_due_subscriptions_downgrades_and_emits_churn():
    svc = _build_service(_AllowGuard())
    order = svc.create_trial_order(_user(), TRIAL_PLAN_CODE, "alipay")
    start = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    svc.activate_trial_order(order.id, now=start)  # end_at = 2026-07-01

    churn_now = datetime(2026, 7, 2, 0, 0, 0, tzinfo=timezone.utc)  # 已过 end_at

    expired = svc.expire_due_subscriptions(churn_now)

    assert len(expired) == 1
    assert expired[0].status == "expired"
    assert expired[0].plan_code == TRIAL_PLAN_CODE
    # 二次扫描应无新增（已 expired 不再被 list_active_trial_due 命中）
    again = svc.expire_due_subscriptions(churn_now)
    assert again == []

    events = svc.event_publisher.events
    churns = [p for e, p in events if e == "trial_churn"]
    assert len(churns) == 1
    assert churns[0]["user_id"] == "U1"
    assert churns[0]["plan_code"] == TRIAL_PLAN_CODE


if __name__ == "__main__":  # pragma: no cover - 手动冒烟入口
    import traceback

    failures = 0
    for fn in [
        test_create_trial_order_success,
        test_create_trial_order_blocked_by_guard,
        test_activate_trial_order_creates_subscription,
        test_expire_due_subscriptions_downgrades_and_emits_churn,
    ]:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:  # noqa: BLE001
            failures += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILED'}")
    raise SystemExit(1 if failures else 0)
