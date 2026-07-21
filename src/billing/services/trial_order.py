"""Task 3: dtcoder 9.9 尝鲜价套餐 — 下单与计费周期服务。

本模块实现尝鲜套餐的下单、支付回调开通、到期降级三条核心链路。

设计要点
--------
* 仓储 / 事件发布 / 风控守卫全部通过构造函数注入（依赖倒置），便于测试
  用 in-memory 仓储与捕获式 EventPublisher stub 独立运行。
* Task1（``TrialPlan``/``TrialPurchaseRecord`` 模型）与 Task2（``TrialGuard``
  风控服务）模块当前可能尚未落盘；若已落盘可优先导入复用，否则使用本模块
  内置的最小 dataclass + ``Protocol`` 接口，保证本 Task 可独立编译与测试。
* 不依赖任何 web/ORM 框架，纯标准库实现。

SSOT 合约摘录
--------------
* plan_code = ``trial-9.9-monthly``，price = 9.90（Decimal），duration_days = 30
* auto_renew = False（到期降级免费版）
* 埋点事件：``trial_activate``（开通）/ ``trial_churn``（到期降级）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Protocol, runtime_checkable

TRIAL_PLAN_CODE = "trial-9.9-monthly"
TRIAL_PRICE = Decimal("9.90")
TRIAL_DURATION_DAYS = 30


# ---------------------------------------------------------------------------
# 领域对象（最小 dataclass；若 Task1 模块已落盘可由其覆盖）
# ---------------------------------------------------------------------------


@dataclass
class User:
    """下单用户。仅保留本 Task 所需字段。"""

    user_id: str
    registered_at: datetime
    ip: str = ""


@dataclass
class Device:
    device_fingerprint: str = ""


@dataclass
class Payment:
    payment_method_hash: str = ""


@dataclass
class TrialOrder:
    """尝鲜订单。"""

    id: str
    user_id: str
    plan_code: str
    amount: Decimal
    status: str  # pending / paid / ...
    created_at: datetime
    payment_channel: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.amount, float):  # 防止 float 污染 Decimal
            self.amount = Decimal(str(self.amount))


@dataclass
class UserSubscription:
    """用户订阅记录。"""

    id: str
    user_id: str
    plan_code: str
    start_at: datetime
    end_at: datetime
    auto_renew: bool
    status: str  # active / expired / ...


@dataclass
class TrialPurchaseRecord:
    """尝鲜购买记录。status: pending / completed / ..."""

    id: str
    user_id: str
    device_fingerprint: str = ""
    payment_method_hash: str = ""
    purchased_at: datetime | None = None
    status: str = "pending"


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class PurchaseNotAllowed(Exception):
    """限购/风控命中时抛出，携带 reason。"""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class OrderNotFound(Exception):
    """支付回调开通时找不到对应订单。"""


# ---------------------------------------------------------------------------
# 注入接口（Protocol）
# ---------------------------------------------------------------------------


@runtime_checkable
class TrialGuard(Protocol):
    def check_purchase_eligibility(
        self, user: User, device: Device, payment: Payment
    ) -> tuple[bool, str]:
        """返回 (allowed, reason)。allowed=False 表示命中拦截。"""
        ...


@runtime_checkable
class OrderRepository(Protocol):
    def save_order(self, order: TrialOrder) -> None: ...

    def get_order(self, order_id: str) -> TrialOrder | None: ...


@runtime_checkable
class SubscriptionRepository(Protocol):
    def save_subscription(self, subscription: UserSubscription) -> None: ...

    def list_active_trial_due(self, now: datetime) -> list[UserSubscription]:
        """返回所有 end_at<=now 且 status='active' 的尝鲜订阅。"""
        ...


@runtime_checkable
class PurchaseRecordRepository(Protocol):
    def save_purchase_record(self, record: TrialPurchaseRecord) -> None: ...


@runtime_checkable
class EventPublisher(Protocol):
    def emit(self, event: str, payload: dict[str, Any]) -> None: ...


# ---------------------------------------------------------------------------
# 默认 in-memory 实现（便于无框架接入与冒烟）
# ---------------------------------------------------------------------------


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[str, TrialOrder] = {}

    def save_order(self, order: TrialOrder) -> None:
        self._orders[order.id] = order

    def get_order(self, order_id: str) -> TrialOrder | None:
        return self._orders.get(order_id)


class InMemorySubscriptionRepository:
    def __init__(self) -> None:
        self._subs: list[UserSubscription] = []

    def save_subscription(self, subscription: UserSubscription) -> None:
        # 替换同 id 旧记录，避免重复
        self._subs = [s for s in self._subs if s.id != subscription.id]
        self._subs.append(subscription)

    def list_active_trial_due(self, now: datetime) -> list[UserSubscription]:
        return [
            s
            for s in self._subs
            if s.plan_code == TRIAL_PLAN_CODE
            and s.status == "active"
            and s.end_at <= now
        ]


class InMemoryPurchaseRecordRepository:
    def __init__(self) -> None:
        self._records: list[TrialPurchaseRecord] = []

    def save_purchase_record(self, record: TrialPurchaseRecord) -> None:
        self._records.append(record)


class CapturingEventPublisher:
    """捕获所有 emit 事件，便于测试断言。"""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def emit(self, event: str, payload: dict[str, Any]) -> None:
        self.events.append((event, dict(payload)))


class AlwaysAllowGuard:
    """默认放行守卫：用于无 Task2 时的冒烟/默认装配。"""

    def check_purchase_eligibility(
        self, user: User, device: Device, payment: Payment
    ) -> tuple[bool, str]:
        return True, "ok"


# ---------------------------------------------------------------------------
# 服务
# ---------------------------------------------------------------------------


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class TrialOrderService:
    """下单与计费周期服务。

    所有依赖通过构造函数注入；缺省值提供 in-memory 默认实现，方便无框架
    装配与冒烟。生产环境应注入真实仓储 / 守卫 / 事件总线。
    """

    def __init__(
        self,
        *,
        guard: TrialGuard | None = None,
        order_repo: OrderRepository | None = None,
        subscription_repo: SubscriptionRepository | None = None,
        purchase_repo: PurchaseRecordRepository | None = None,
        event_publisher: EventPublisher | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.guard: TrialGuard = guard if guard is not None else AlwaysAllowGuard()
        self.order_repo: OrderRepository = (
            order_repo if order_repo is not None else InMemoryOrderRepository()
        )
        self.subscription_repo: SubscriptionRepository = (
            subscription_repo
            if subscription_repo is not None
            else InMemorySubscriptionRepository()
        )
        self.purchase_repo: PurchaseRecordRepository = (
            purchase_repo
            if purchase_repo is not None
            else InMemoryPurchaseRecordRepository()
        )
        self.event_publisher: EventPublisher = (
            event_publisher if event_publisher is not None else CapturingEventPublisher()
        )
        self._clock: Callable[[], datetime] = clock if clock is not None else _utcnow

    # ---- 下单 ----

    def create_trial_order(
        self,
        user: User,
        plan_code: str = TRIAL_PLAN_CODE,
        payment_channel: str = "",
        *,
        device: Device | None = None,
        payment: Payment | None = None,
    ) -> TrialOrder:
        """创建尝鲜订单。

        调用 Task2 风控守卫；命中拦截抛 ``PurchaseNotAllowed(reason)``。
        通过则生成 ``TrialOrder``（status=pending）并持久化。
        """
        allowed, reason = self.guard.check_purchase_eligibility(
            user, device or Device(), payment or Payment()
        )
        if not allowed:
            raise PurchaseNotAllowed(reason)

        order = TrialOrder(
            id=_new_id("order"),
            user_id=user.user_id,
            plan_code=plan_code,
            amount=TRIAL_PRICE,
            status="pending",
            created_at=self._clock(),
            payment_channel=payment_channel,
        )
        self.order_repo.save_order(order)
        return order

    # ---- 支付回调开通 ----

    def activate_trial_order(self, order_id: str, *, now: datetime | None = None) -> UserSubscription:
        """支付回调开通尝鲜订阅。

        1. 取回 pending 订单（找不到抛 ``OrderNotFound``）。
        2. 写 ``UserSubscription``（start_at=now, end_at=now+30d,
           auto_renew=False, status=active）。
        3. 写 ``TrialPurchaseRecord``（status=completed）。
        4. 发 ``trial_activate`` 埋点。
        """
        moment = now if now is not None else self._clock()

        order = self.order_repo.get_order(order_id)
        if order is None:
            raise OrderNotFound(order_id)

        start_at = moment
        end_at = moment + timedelta(days=TRIAL_DURATION_DAYS)
        subscription = UserSubscription(
            id=_new_id("sub"),
            user_id=order.user_id,
            plan_code=TRIAL_PLAN_CODE,
            start_at=start_at,
            end_at=end_at,
            auto_renew=False,
            status="active",
        )
        self.subscription_repo.save_subscription(subscription)

        record = TrialPurchaseRecord(
            id=_new_id("purchase"),
            user_id=order.user_id,
            purchased_at=moment,
            status="completed",
        )
        self.purchase_repo.save_purchase_record(record)

        # 订单状态推进为 paid
        paid_order = replace(order, status="paid")
        self.order_repo.save_order(paid_order)

        self.event_publisher.emit(
            "trial_activate",
            {
                "user_id": order.user_id,
                "order_id": order.id,
                "plan_code": TRIAL_PLAN_CODE,
                "subscription_id": subscription.id,
                "end_at": end_at.isoformat(),
            },
        )
        return subscription

    # ---- 到期降级 ----

    def expire_due_subscriptions(self, now: datetime) -> list[UserSubscription]:
        """扫描 end_at<=now 且 active 的尝鲜订阅 → 降级 expired + 发 trial_churn。

        返回本次被降级的订阅列表。
        """
        due = self.subscription_repo.list_active_trial_due(now)
        expired: list[UserSubscription] = []
        for sub in due:
            updated = replace(sub, status="expired")
            self.subscription_repo.save_subscription(updated)
            expired.append(updated)
            self.event_publisher.emit(
                "trial_churn",
                {
                    "user_id": sub.user_id,
                    "subscription_id": sub.id,
                    "plan_code": sub.plan_code,
                    "end_at": sub.end_at.isoformat(),
                },
            )
        return expired


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 模块级默认服务（供 api/order.py 与无依赖调用方使用）
# ---------------------------------------------------------------------------

_default_service = TrialOrderService()


def create_trial_order(
    user: User,
    plan_code: str = TRIAL_PLAN_CODE,
    payment_channel: str = "",
    *,
    device: Device | None = None,
    payment: Payment | None = None,
) -> TrialOrder:
    """模块级便捷入口：委托默认 in-memory 服务。

    生产环境请直接构造 ``TrialOrderService`` 注入真实依赖，或由
    ``src/billing/api/order.py`` 装配 DI 容器后调用。
    """
    return _default_service.create_trial_order(
        user, plan_code, payment_channel, device=device, payment=payment
    )


def activate_trial_order(order_id: str, *, now: datetime | None = None) -> UserSubscription:
    return _default_service.activate_trial_order(order_id, now=now)


def expire_due_subscriptions(now: datetime) -> list[UserSubscription]:
    return _default_service.expire_due_subscriptions(now)
