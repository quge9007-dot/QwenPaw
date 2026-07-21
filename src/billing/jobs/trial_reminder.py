"""到期提醒与转化钩子 — dtcoder 9.9 尝鲜价套餐 Task 5.

扫描 ``end_at - now ∈ {7,3,1}`` 天的 active 尝鲜订阅（``plan_code='trial-9.9-monthly'``），
按触点发提醒（站内信必发、邮件按用户偏好、推送），并在 7 天提醒附正价满减券（满 99 减 30）、
1 天提醒附年付 8 折入口。每次有效提醒均发 ``trial_renew_prompt`` 埋点。

去重：每条订阅记录 ``reminder_days_sent`` 已发提醒的天数集合，同一窗口只发一次。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from src.billing.services.conversion_coupon import (
    COUPON_TYPE_ANNUAL_DISCOUNT,
    COUPON_TYPE_DISCOUNT_FULL,
    issue_conversion_coupon,
)

# SSOT 套餐标识
TRIAL_PLAN_CODE = "trial-9.9-monthly"

# 提醒触点窗口（end_at - now 的天数）
REMINDER_DAYS = (7, 3, 1)

# 窗口 → 转化券类型；3 天提醒无券（纯提醒）
WINDOW_COUPON: dict[int, str] = {
    7: COUPON_TYPE_DISCOUNT_FULL,
    1: COUPON_TYPE_ANNUAL_DISCOUNT,
}

RENEW_PROMPT_EVENT = "trial_renew_prompt"

# 触达渠道
CHANNEL_INAPP = "inapp"
CHANNEL_EMAIL = "email"
CHANNEL_PUSH = "push"


@dataclass
class UserSubscription:
    """尝鲜订阅记录（轻量自洽，便于内存仓储与测试）。"""

    id: str
    user_id: str
    plan_code: str
    start_at: datetime
    end_at: datetime
    auto_renew: bool = False
    status: str = "active"
    # 已发提醒的天数集合，用于幂等去重
    reminder_days_sent: set[int] = field(default_factory=set)

    def is_active_trial(self) -> bool:
        return self.status == "active" and self.plan_code == TRIAL_PLAN_CODE

    def days_to_end(self, now: datetime) -> int:
        return (self.end_at - now).days


@dataclass
class UserContact:
    """用户触达偏好（用于邮件/推送分流）。"""

    user_id: str
    email: str | None = None
    email_opt_in: bool = False
    push_token: str | None = None


# 协议（可注入 in-memory 实现 / 捕获式 stub） --------------------------------
class SubscriptionRepo(Protocol):  # pragma: no cover - protocol
    def list_active_trial_subscriptions(self, plan_code: str) -> list[UserSubscription]:
        ...

    def get_user(self, user_id: str) -> UserContact | None:
        ...

    def save(self, subscription: UserSubscription) -> None:
        ...


class Notifier(Protocol):  # pragma: no cover - protocol
    def send(self, user_id: str, channel: str, subject: str, body: str, extras: dict | None = None) -> None:
        ...


class CouponService(Protocol):  # pragma: no cover - protocol
    def issue_conversion_coupon(
        self, user: Any, coupon_type: str, value: Decimal | None = None
    ) -> Any:
        ...


class EventPublisher(Protocol):  # pragma: no cover - protocol
    def publish(self, event: str, payload: dict) -> None:
        ...


class _DefaultCouponService:
    """默认 coupon_service：直接调用 issue_conversion_coupon（无仓储持久化）。"""

    def issue_conversion_coupon(
        self, user: Any, coupon_type: str, value: Decimal | None = None
    ) -> Any:
        return issue_conversion_coupon(user, coupon_type, value)


def _reminder_message(days_to_end: int) -> tuple[str, str]:
    """返回 (subject, body) 提醒文案。"""
    if days_to_end == 7:
        return (
            "dtcoder 尝鲜版即将到期",
            "您的尝鲜版订阅将在 7 天后到期，续订可享正价满减券（满 99 减 30）。",
        )
    if days_to_end == 3:
        return (
            "dtcoder 尝鲜版 3 天后到期",
            "您的尝鲜版订阅将在 3 天后到期，记得续订继续使用。",
        )
    # 1 天
    return (
        "dtcoder 尝鲜版明天到期",
        "您的尝鲜版订阅明天到期，年付 8 折入口已为您准备好。",
    )


def _deliver(
    notifier: Notifier,
    user: UserContact,
    subject: str,
    body: str,
    extras: dict | None = None,
) -> list[str]:
    """按触点分发提醒，返回已送达渠道列表。

    站内信必发；邮件按用户偏好（email_opt_in）；推送按 push_token 存在。
    """
    sent: list[str] = []

    # 站内信必发
    notifier.send(user.user_id, CHANNEL_INAPP, subject, body, extras)
    sent.append(CHANNEL_INAPP)

    # 邮件按偏好
    if user.email and user.email_opt_in:
        notifier.send(user.user_id, CHANNEL_EMAIL, subject, body, extras)
        sent.append(CHANNEL_EMAIL)

    # 推送
    if user.push_token:
        notifier.send(user.user_id, CHANNEL_PUSH, subject, body, extras)
        sent.append(CHANNEL_PUSH)

    return sent


def run_trial_reminders(
    now: datetime,
    subscription_repo: SubscriptionRepo,
    notifier: Notifier,
    coupon_service: CouponService | None = None,
    event_publisher: EventPublisher | None = None,
) -> list[dict]:
    """扫描 active 尝鲜订阅，按窗口发到期提醒与转化券，发埋点。

    :return: 本次实际触发的提醒记录列表（便于断言/日志）。
    """
    coupon_service = coupon_service or _DefaultCouponService()
    results: list[dict] = []

    subs = subscription_repo.list_active_trial_subscriptions(TRIAL_PLAN_CODE)
    for sub in subs:
        if not sub.is_active_trial():
            continue

        days_to_end = sub.days_to_end(now)
        if days_to_end not in REMINDER_DAYS:
            continue
        # 幂等去重：同一窗口已发则跳过
        if days_to_end in sub.reminder_days_sent:
            continue

        user = subscription_repo.get_user(sub.user_id)
        if user is None:
            # 无触达偏好仍兜底发站内信：构造最小 contact
            user = UserContact(user_id=sub.user_id)

        subject, body = _reminder_message(days_to_end)

        # 转化券
        coupon = None
        coupon_type = WINDOW_COUPON.get(days_to_end)
        if coupon_type is not None:
            coupon = coupon_service.issue_conversion_coupon(user, coupon_type)

        extras = {
            "plan_code": sub.plan_code,
            "days_to_end": days_to_end,
            "subscription_id": sub.id,
        }
        if coupon is not None:
            extras["coupon_id"] = getattr(coupon, "id", None)
            extras["coupon_type"] = coupon_type

        sent_channels = _deliver(notifier, user, subject, body, extras)

        # 埋点：trial_renew_prompt
        if event_publisher is not None:
            event_publisher.publish(
                RENEW_PROMPT_EVENT,
                {
                    "user_id": sub.user_id,
                    "subscription_id": sub.id,
                    "plan_code": sub.plan_code,
                    "days_to_end": days_to_end,
                    "channels": sent_channels,
                    "coupon_type": coupon_type,
                    "coupon_id": extras.get("coupon_id"),
                    "auto_renew": sub.auto_renew,
                },
            )

        # 记录已发，落库去重
        sub.reminder_days_sent.add(days_to_end)
        subscription_repo.save(sub)

        results.append(
            {
                "subscription_id": sub.id,
                "user_id": sub.user_id,
                "days_to_end": days_to_end,
                "channels": sent_channels,
                "coupon_type": coupon_type,
                "coupon_id": extras.get("coupon_id"),
            }
        )

    return results
