# -*- coding: utf-8 -*-
"""Task 2 —— 限购与风控校验服务 TDD 用例。

6 用例：首次可购、重复账号拦截、重复设备拦截、重复支付拦截、
新注册延迟标记(delayed_activation)、IP 限流拦截。仓储用 in-memory stub 注入。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 让测试在未安装包时也能直接 import（src/ 平铺布局）。
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from billing.services.trial_guard import (  # noqa: E402
    InMemoryPurchaseRecordRepo,
    RiskEvent,
    TrialPurchaseRecord,
    check_purchase_eligibility,
)


# -----------------------------------------------------------------------------
# 轻量输入对象（仅含 SSOT 约定的字段）
# -----------------------------------------------------------------------------


@dataclass
class _User:
    user_id: str
    registered_at: datetime
    ip: str


@dataclass
class _Device:
    device_fingerprint: str


@dataclass
class _Payment:
    payment_method_hash: str


_NOW = datetime(2026, 7, 21, 6, 0, 0, tzinfo=timezone.utc)


def _user(uid: str = "u1", registered_hours_ago: float = 48.0, ip: str = "10.0.0.1"):
    return _User(
        user_id=uid,
        registered_at=_NOW - timedelta(hours=registered_hours_ago),
        ip=ip,
    )


def _device(fp: str = "fp-1"):
    return _Device(device_fingerprint=fp)


def _payment(pm: str = "pm-1"):
    return _Payment(payment_method_hash=pm)


def _record(uid="u0", fp="fp-0", pm="pm-0", ip="10.0.0.1", purchased_at=None):
    return TrialPurchaseRecord(
        user_id=uid,
        device_fingerprint=fp,
        payment_method_hash=pm,
        purchased_at=purchased_at or _NOW,
        ip=ip,
    )


# -----------------------------------------------------------------------------
# 用例 1：首次可购
# -----------------------------------------------------------------------------


def test_first_purchase_allowed():
    repo = InMemoryPurchaseRecordRepo(records=[])
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(), _device(), _payment(), repo, now=_NOW, risk_events=events
    )
    assert allowed is True
    assert reason == "ok"
    # 写入一条 eligible RiskEvent
    assert len(events) == 1
    assert events[0].event_type == "eligible"


# -----------------------------------------------------------------------------
# 用例 2：重复账号拦截
# -----------------------------------------------------------------------------


def test_duplicate_user_blocked():
    repo = InMemoryPurchaseRecordRepo(
        records=[_record(uid="u1", fp="fp-x", pm="pm-x")]
    )
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(uid="u1"), _device(), _payment(), repo, now=_NOW, risk_events=events
    )
    assert allowed is False
    assert reason == "duplicate_user"
    assert events[0].event_type == "duplicate_user"


# -----------------------------------------------------------------------------
# 用例 3：重复设备拦截
# -----------------------------------------------------------------------------


def test_duplicate_device_blocked():
    repo = InMemoryPurchaseRecordRepo(
        records=[_record(uid="u-other", fp="fp-1", pm="pm-x")]
    )
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(uid="u-new"), _device(fp="fp-1"), _payment(), repo, now=_NOW, risk_events=events
    )
    assert allowed is False
    assert reason == "duplicate_device"


# -----------------------------------------------------------------------------
# 用例 4：重复支付拦截
# -----------------------------------------------------------------------------


def test_duplicate_payment_blocked():
    # 该支付方式已绑定 1 个其它 user_id（<2，未触发 manual_review）→ duplicate_payment
    repo = InMemoryPurchaseRecordRepo(
        records=[_record(uid="u-a", fp="fp-a", pm="pm-1")]
    )
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(uid="u-b"), _device(fp="fp-b"), _payment(pm="pm-1"),
        repo, now=_NOW, risk_events=events,
    )
    assert allowed is False
    assert reason == "duplicate_payment"
    assert events[0].event_type == "duplicate_payment"


# -----------------------------------------------------------------------------
# 用例 5：新注册延迟标记（不拦截）
# -----------------------------------------------------------------------------


def test_new_user_delayed_activation():
    repo = InMemoryPurchaseRecordRepo(records=[])
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(uid="u-fresh", registered_hours_ago=2.0),
        _device(fp="fp-fresh"),
        _payment(pm="pm-fresh"),
        repo,
        now=_NOW,
        risk_events=events,
    )
    assert allowed is True
    assert reason == "delayed_activation"
    assert events[-1].event_type == "delayed_activation"


# -----------------------------------------------------------------------------
# 用例 6：同 IP 段 24h 成交 ≥5 → 限流拦截
# -----------------------------------------------------------------------------


def test_ip_throttle_blocked():
    # 同 /24 段已有 5 笔成交，新用户再购 → ip_throttle
    seed = [
        _record(uid=f"u{i}", fp=f"fp{i}", pm=f"pm{i}", ip="10.0.0.5")
        for i in range(5)
    ]
    repo = InMemoryPurchaseRecordRepo(records=seed)
    events: list = []
    allowed, reason = check_purchase_eligibility(
        _user(uid="u-new", registered_hours_ago=48.0, ip="10.0.0.9"),
        _device(fp="fp-new"),
        _payment(pm="pm-new"),
        repo,
        now=_NOW,
        risk_events=events,
    )
    assert allowed is False
    assert reason == "ip_throttle"
    assert events[0].event_type == "ip_throttle"
