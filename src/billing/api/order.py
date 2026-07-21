"""Task 3: dtcoder 9.9 尝鲜价套餐 — 下单 API 入口。

本模块为下单链路提供「纯函数 + 注释说明接入点」的入口层，**不依赖任何
web 框架**（FastAPI/Flask/CLI 框架均未引入）。生产环境可在此处接入：

HTTP 接入点（示例伪代码，未引入框架）::

    # FastAPI / Flask 等路由层把请求适配为下列函数调用：
    @app.post("/billing/trial/orders")
    def http_create_trial_order(request):
        user = _map_request_user(request)          # 解析 user_id / ip / registered_at
        order = create_trial_order_api(
            user=user,
            plan_code=request["plan_code"],
            payment_channel=request["payment_channel"],
        )
        return {"order_id": order.id, "amount": str(order.amount)}

    # 支付回调（异步 webhook）开通：
    @app.post("/billing/trial/orders/{order_id}/activate")
    def http_activate(order_id: str):
        sub = activate_trial_order_api(order_id)
        return {"subscription_id": sub.id, "end_at": sub.end_at.isoformat()}

CLI 接入点（示例伪代码）::

    # qwenpaw billing trial create --user U1 --channel alipay
    # qwenpaw billing trial activate --order-id order_xxx
    # qwenpaw billing trial expire          # 定时任务触发到期降级

注入装配
--------
真实部署应构造 ``TrialOrderService`` 时注入：DB-backed 仓储（OrderRepository /
SubscriptionRepository / PurchaseRecordRepository）、Task2 的 ``TrialGuard``、
消息总线 ``EventPublisher``。本模块的便捷函数默认使用 in-memory 装配，仅用于
冒烟与开发态；生产调用方请走 ``build_service(...)`` 自行注入。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from billing.services.trial_order import (
    AlwaysAllowGuard,
    CapturingEventPublisher,
    InMemoryOrderRepository,
    InMemoryPurchaseRecordRepository,
    InMemorySubscriptionRepository,
    TRIAL_PLAN_CODE,
    TrialOrder,
    TrialOrderService,
    UserSubscription,
)

# 模块级默认服务（in-memory），供无 DI 容器的调用方冒烟使用。
_default_service: TrialOrderService | None = None


def build_service(
    *,
    guard: Any = None,
    order_repo: Any = None,
    subscription_repo: Any = None,
    purchase_repo: Any = None,
    event_publisher: Any = None,
    clock: Callable[[], datetime] | None = None,
) -> TrialOrderService:
    """构造注入真实依赖的 ``TrialOrderService``。

    生产代码应在应用启动时调用本函数（或等价 DI 装配），将 DB 仓储、
    风控守卫、事件总线注入；缺省参数回落到 in-memory 默认实现。
    """
    return TrialOrderService(
        guard=guard,
        order_repo=order_repo,
        subscription_repo=subscription_repo,
        purchase_repo=purchase_repo,
        event_publisher=event_publisher,
        clock=clock,
    )


def _get_default_service() -> TrialOrderService:
    global _default_service  # noqa: PLW0603
    if _default_service is None:
        _default_service = TrialOrderService(
            guard=AlwaysAllowGuard(),
            order_repo=InMemoryOrderRepository(),
            subscription_repo=InMemorySubscriptionRepository(),
            purchase_repo=InMemoryPurchaseRecordRepository(),
            event_publisher=CapturingEventPublisher(),
        )
    return _default_service


def create_trial_order_api(
    user: Any,
    plan_code: str = TRIAL_PLAN_CODE,
    payment_channel: str = "",
) -> TrialOrder:
    """下单入口。HTTP/CLI 适配层把请求映射为对它的调用。"""
    return _get_default_service().create_trial_order(user, plan_code, payment_channel)


def activate_trial_order_api(order_id: str, *, now: datetime | None = None) -> UserSubscription:
    """支付回调开通入口。"""
    return _get_default_service().activate_trial_order(order_id, now=now)


def expire_due_subscriptions_api(now: datetime) -> list[UserSubscription]:
    """到期降级入口（定时任务 / cron 触发）。"""
    return _get_default_service().expire_due_subscriptions(now)
