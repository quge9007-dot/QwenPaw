"""Task 5 TDD — 到期提醒与转化钩子。

仅依赖标准库 + 本仓库新建模块（in-memory 仓储 + 捕获式 stub），无外部服务。

用例：
1. 到期前 7 天 → 触发提醒 + 发放满 99 减 30 券 + 发 trial_renew_prompt 埋点。
2. 到期前 1 天 → 触发提醒 + 发年付 8 折入口券。
3. 触达渠道选择：站内信必发，邮件按用户偏好（关闭时不发邮件），且窗口内幂等不重发。
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 让 `src.*` 命名空间包可被导入（本任务未新增 __init__.py，遵循硬约束）
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.billing.jobs.trial_reminder import (  # noqa: E402
    CHANNEL_EMAIL,
    CHANNEL_INAPP,
    CHANNEL_PUSH,
    RENEW_PROMPT_EVENT,
    TRIAL_PLAN_CODE,
    UserContact,
    UserSubscription,
    run_trial_reminders,
)
from src.billing.services.conversion_coupon import (  # noqa: E402
    ANNUAL_DISCOUNT_VALUE,
    COUPON_TYPE_ANNUAL_DISCOUNT,
    COUPON_TYPE_DISCOUNT_FULL,
    DISCOUNT_FULL_MIN_SPEND,
    DISCOUNT_FULL_VALUE,
    issue_conversion_coupon,
)


# ---------------------------------------------------------------------------
# 捕获式 stub / in-memory 仓储
# ---------------------------------------------------------------------------


class InMemorySubscriptionRepo:
    def __init__(self, subs, users):
        self._subs = list(subs)
        self._users = {u.user_id: u for u in users}
        self.save_calls: list[UserSubscription] = []

    def list_active_trial_subscriptions(self, plan_code):
        return [s for s in self._subs if s.plan_code == plan_code and s.status == "active"]

    def get_user(self, user_id):
        return self._users.get(user_id)

    def save(self, subscription):
        # 真实落库语义：原地更新已发集合
        self.save_calls.append(subscription)


class CapturingNotifier:
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, user_id, channel, subject, body, extras=None):
        self.sent.append(
            {
                "user_id": user_id,
                "channel": channel,
                "subject": subject,
                "body": body,
                "extras": extras,
            }
        )


class CapturingCouponService:
    """捕获 issue_conversion_coupon 调用，并产出带 id 的轻量券对象。"""

    def __init__(self):
        self.calls: list[dict] = []
        self._seq = 0

    def issue_conversion_coupon(self, user, coupon_type, value=None):
        self._seq += 1
        coupon_id = f"cpn_stub_{self._seq}"
        self.calls.append(
            {"user": user, "coupon_type": coupon_type, "value": value, "coupon_id": coupon_id}
        )

        class _Coupon:
            id = coupon_id

        return _Coupon()


class CapturingEventPublisher:
    def __init__(self):
        self.events: list[dict] = []

    def publish(self, event, payload):
        self.events.append({"event": event, "payload": payload})


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------


def _make_sub(user_id, end_at, now, reminder_days_sent=None):
    return UserSubscription(
        id=f"sub_{user_id}",
        user_id=user_id,
        plan_code=TRIAL_PLAN_CODE,
        start_at=now - timedelta(days=23),
        end_at=end_at,
        auto_renew=False,
        status="active",
        reminder_days_sent=set(reminder_days_sent or set()),
    )


NOW = datetime(2026, 7, 21, 6, 0, 0)


# ---------------------------------------------------------------------------
# 用例 1：到期前 7 天 → 提醒 + 满 99 减 30 券 + 埋点
# ---------------------------------------------------------------------------


def test_seven_day_reminder_issues_discount_full_coupon_and_event():
    end_at = NOW + timedelta(days=7)
    sub = _make_sub("u1", end_at, NOW)
    user = UserContact(
        user_id="u1", email="u1@example.com", email_opt_in=True, push_token="tok-u1"
    )
    repo = InMemorySubscriptionRepo([sub], [user])
    notifier = CapturingNotifier()
    coupon_service = CapturingCouponService()
    publisher = CapturingEventPublisher()

    results = run_trial_reminders(NOW, repo, notifier, coupon_service, publisher)

    # 触发了一条提醒
    assert len(results) == 1
    r = results[0]
    assert r["days_to_end"] == 7
    assert r["coupon_type"] == COUPON_TYPE_DISCOUNT_FULL

    # 站内信 + 邮件（偏好开启）+ 推送 均送达
    channels = [m["channel"] for m in notifier.sent]
    assert CHANNEL_INAPP in channels
    assert CHANNEL_EMAIL in channels
    assert CHANNEL_PUSH in channels

    # coupon_service 被调用一次，类型=discount_full
    assert len(coupon_service.calls) == 1
    call = coupon_service.calls[0]
    assert call["coupon_type"] == COUPON_TYPE_DISCOUNT_FULL

    # 埋点：trial_renew_prompt，含 days_to_end 与 coupon 信息
    assert len(publisher.events) == 1
    ev = publisher.events[0]
    assert ev["event"] == RENEW_PROMPT_EVENT
    assert ev["payload"]["days_to_end"] == 7
    assert ev["payload"]["coupon_type"] == COUPON_TYPE_DISCOUNT_FULL
    assert ev["payload"]["coupon_id"] is not None

    # 幂等：同一窗口再跑不发
    results2 = run_trial_reminders(NOW, repo, notifier, coupon_service, publisher)
    assert results2 == []
    assert len(coupon_service.calls) == 1  # 没多发券
    assert len(publisher.events) == 1  # 没多埋点

    # 落库记录已发天数集合
    assert sub.reminder_days_sent == {7}
    assert repo.save_calls  # 确实 save 过


# ---------------------------------------------------------------------------
# 用例 2：到期前 1 天 → 年付 8 折入口券
# ---------------------------------------------------------------------------


def test_one_day_reminder_issues_annual_discount_coupon():
    end_at = NOW + timedelta(days=1)
    sub = _make_sub("u2", end_at, NOW)
    user = UserContact(user_id="u2", push_token="tok-u2")  # 无邮件偏好
    repo = InMemorySubscriptionRepo([sub], [user])
    notifier = CapturingNotifier()
    coupon_service = CapturingCouponService()
    publisher = CapturingEventPublisher()

    results = run_trial_reminders(NOW, repo, notifier, coupon_service, publisher)

    assert len(results) == 1
    r = results[0]
    assert r["days_to_end"] == 1
    assert r["coupon_type"] == COUPON_TYPE_ANNUAL_DISCOUNT

    assert len(coupon_service.calls) == 1
    assert coupon_service.calls[0]["coupon_type"] == COUPON_TYPE_ANNUAL_DISCOUNT

    assert len(publisher.events) == 1
    assert publisher.events[0]["payload"]["coupon_type"] == COUPON_TYPE_ANNUAL_DISCOUNT


# ---------------------------------------------------------------------------
# 用例 3：触达渠道选择（站内信必发，邮件按偏好关闭不发）
# ---------------------------------------------------------------------------


def test_channel_selection_inapp_always_email_by_preference():
    # 3 天提醒（无券，聚焦渠道分流）；用户关闭邮件偏好
    end_at = NOW + timedelta(days=3)
    sub = _make_sub("u3", end_at, NOW)
    user = UserContact(
        user_id="u3", email="u3@example.com", email_opt_in=False, push_token="tok-u3"
    )
    repo = InMemorySubscriptionRepo([sub], [user])
    notifier = CapturingNotifier()
    coupon_service = CapturingCouponService()
    publisher = CapturingEventPublisher()

    results = run_trial_reminders(NOW, repo, notifier, coupon_service, publisher)

    assert len(results) == 1
    channels = [m["channel"] for m in notifier.sent]
    assert CHANNEL_INAPP in channels  # 站内信必发
    assert CHANNEL_EMAIL not in channels  # 邮件偏好关闭 → 不发
    assert CHANNEL_PUSH in channels  # 推送（有 push_token）
    assert results[0]["coupon_type"] is None  # 3 天无券


# ---------------------------------------------------------------------------
# 附加：conversion_coupon 模块单元校验（SSOT 默认值）
# ---------------------------------------------------------------------------


def test_issue_conversion_coupon_ssot_defaults():
    user = UserContact(user_id="uX", email="x@example.com", email_opt_in=True)

    c1 = issue_conversion_coupon(user, COUPON_TYPE_DISCOUNT_FULL)
    assert c1.type == COUPON_TYPE_DISCOUNT_FULL
    assert c1.value == DISCOUNT_FULL_VALUE == Decimal("30")
    assert c1.min_spend == DISCOUNT_FULL_MIN_SPEND == Decimal("99")
    assert c1.status == "active"
    assert c1.user_id == "uX"

    c2 = issue_conversion_coupon(user, COUPON_TYPE_ANNUAL_DISCOUNT)
    assert c2.type == COUPON_TYPE_ANNUAL_DISCOUNT
    assert c2.value == ANNUAL_DISCOUNT_VALUE == Decimal("0.2")
    assert c2.min_spend is None
    assert c2.status == "active"
