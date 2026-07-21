# -*- coding: utf-8 -*-
"""dtcoder 9.9 尝鲜价套餐 —— 限购与风控校验服务（Task 2）。

本模块实现 ``check_purchase_eligibility``，承担三重去重 + 风控阈值校验，
并在每次决策时写入 ``RiskEvent`` 审计记录。

设计说明
--------
* Task 1（``src/billing/models/trial_plan.py``）在当前仓库尚未落盘，按
  本 Task 硬约束「避免改 Task1 文件」，这里在模块内定义最小可用的
  ``TrialPurchaseRecord`` / ``RiskEvent`` dataclass 与仓储接口
  ``PurchaseRecordRepo``，并提供 ``InMemoryPurchaseRecordRepo`` 实现，
  便于测试与下单服务注入。Task 1 落盘后可平滑替换为真实模型。
* 仓储接口仅暴露 SSOT 要求的四个查询方法：
  ``find_by_user_id`` / ``find_by_device`` / ``find_by_payment`` /
  ``count_by_ip_segment_since``。manual_review 所需「同支付绑定 ≥2 不同
  user_id」由 ``find_by_payment`` 返回的记录推导得出，无需新增方法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Protocol, runtime_checkable


# =============================================================================
# 数据模型（最小实现，Task1 落盘后可替换）
# =============================================================================


@dataclass
class TrialPurchaseRecord:
    """尝鲜套餐历史成交记录。"""

    user_id: str
    device_fingerprint: str
    payment_method_hash: str
    purchased_at: datetime
    status: str = "completed"
    # 风控需要按 IP 段聚合，故记录携带购买时的 IP（与 user.ip 一致）。
    ip: str = ""


@dataclass
class RiskEvent:
    """风控决策审计事件。"""

    event_type: str
    payload: dict
    created_at: datetime


# =============================================================================
# 仓储接口（可注入，便于测试与下单服务替换实现）
# =============================================================================


@runtime_checkable
class PurchaseRecordRepo(Protocol):
    """历史成交记录仓储接口。"""

    def find_by_user_id(self, user_id: str) -> List[TrialPurchaseRecord]:
        """按 user_id 查询历史成交。"""

    def find_by_device(self, device_fingerprint: str) -> List[TrialPurchaseRecord]:
        """按设备指纹查询历史成交。"""

    def find_by_payment(self, payment_method_hash: str) -> List[TrialPurchaseRecord]:
        """按支付方式哈希查询历史成交。"""

    def count_by_ip_segment_since(
        self, ip_segment: str, since: datetime
    ) -> int:
        """统计指定 IP 段在 ``since`` 之后成交的单数。"""


class InMemoryPurchaseRecordRepo:
    """基于内存列表的仓储实现，供测试与下单服务注入。

    可选 ``records`` 初始数据；``add`` 用于运行期追加（如开通成功后回写）。
    """

    def __init__(self, records: Optional[Iterable[TrialPurchaseRecord]] = None) -> None:
        self._records: List[TrialPurchaseRecord] = list(records or [])

    def add(self, record: TrialPurchaseRecord) -> None:
        self._records.append(record)

    @staticmethod
    def _same_ip_segment(ip: str, segment: str) -> bool:
        return ip_to_segment(ip) == segment

    def find_by_user_id(self, user_id: str) -> List[TrialPurchaseRecord]:
        return [r for r in self._records if r.user_id == user_id]

    def find_by_device(self, device_fingerprint: str) -> List[TrialPurchaseRecord]:
        return [r for r in self._records if r.device_fingerprint == device_fingerprint]

    def find_by_payment(self, payment_method_hash: str) -> List[TrialPurchaseRecord]:
        return [r for r in self._records if r.payment_method_hash == payment_method_hash]

    def count_by_ip_segment_since(self, ip_segment: str, since: datetime) -> int:
        return sum(
            1
            for r in self._records
            if r.purchased_at >= since and self._same_ip_segment(r.ip, ip_segment)
        )


# =============================================================================
# 辅助
# =============================================================================


def ip_to_segment(ip: str) -> str:
    """将 IPv4 归并到 /24 段（取前三段）。

    非 IPv4 或异常输入退化为整段字符串，保证不抛异常。
    """
    if not ip:
        return ""
    parts = ip.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return ".".join(parts[:3]) + ".0/24"
    return ip


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# =============================================================================
# 核心校验
# =============================================================================


def check_purchase_eligibility(
    user,
    device,
    payment,
    repo: PurchaseRecordRepo,
    *,
    now: Optional[datetime] = None,
    risk_events: Optional[List[RiskEvent]] = None,
) -> tuple:
    """校验尝鲜价购买资格。

    Args:
        user: 含 ``user_id`` / ``registered_at`` / ``ip``。
        device: 含 ``device_fingerprint``。
        payment: 含 ``payment_method_hash``。
        repo: 历史成交仓储（可注入 in-memory stub）。
        now: 当前时间（测试可注入；默认 UTC now）。
        risk_events: 风控事件收集列表，若提供则追加 ``RiskEvent``。

    Returns:
        ``(allowed: bool, reason: str)``。``allowed=True`` 时 reason 为
        ``"ok"`` 或 ``"delayed_activation"``（新注册延迟到账，不拦截）；
        ``allowed=False`` 时 reason 为 ``duplicate_user`` /
        ``duplicate_device`` / ``duplicate_payment`` / ``manual_review`` /
        ``ip_throttle``。
    """
    now = now or _utcnow()
    sink = risk_events if risk_events is not None else []
    user_id = user.user_id
    device_fp = device.device_fingerprint
    pay_hash = payment.payment_method_hash
    ip = getattr(user, "ip", "") or ""
    registered_at = user.registered_at

    def record_event(event_type: str, payload: dict) -> None:
        sink.append(
            RiskEvent(event_type=event_type, payload=dict(payload), created_at=now)
        )

    # --- 1) 三重去重：任一命中即拦截 -------------------------------------
    if repo.find_by_user_id(user_id):
        record_event(
            "duplicate_user",
            {"user_id": user_id, "device_fingerprint": device_fp},
        )
        return False, "duplicate_user"

    if repo.find_by_device(device_fp):
        record_event(
            "duplicate_device",
            {"device_fingerprint": device_fp, "user_id": user_id},
        )
        return False, "duplicate_device"

    pay_records = repo.find_by_payment(pay_hash)
    distinct_users = {r.user_id for r in pay_records}

    # --- 2) 同一支付方式已绑定 ≥2 不同 user_id → 人工复核 ----------------
    # 须先于 duplicate_payment 判定，否则该规则不可达：duplicate_payment 在
    # 「已有任一绑定」时即拦截，无法区分「单次绑定」与「多账号绑定」。
    if len(distinct_users) >= 2:
        record_event(
            "manual_review",
            {
                "payment_method_hash": pay_hash,
                "bound_users": sorted(distinct_users),
                "current_user": user_id,
            },
        )
        return False, "manual_review"

    # --- 3) payment_method_hash 任一命中 → 重复支付拦截 ------------------
    if pay_records:
        record_event(
            "duplicate_payment",
            {"payment_method_hash": pay_hash, "user_id": user_id},
        )
        return False, "duplicate_payment"

    # --- 4) 同 IP 段 24h 成交 ≥5 → 限流 ---------------------------------
    segment = ip_to_segment(ip)
    since = now - timedelta(hours=24)
    ip_count = repo.count_by_ip_segment_since(segment, since)
    if ip_count >= 5:
        record_event(
            "ip_throttle",
            {"ip_segment": segment, "count_24h": ip_count, "user_id": user_id},
        )
        return False, "ip_throttle"

    # --- 5) 新注册 <24h → 延迟到账（不拦截） -----------------------------
    if registered_at is not None:
        # 兼容 aware/naive datetime：若 registered_at 带 tz 而 now 不带（或反之），
        # 统一去掉 tzinfo 做比较，避免 TypeError。
        reg = registered_at
        cmp_now = now
        if getattr(reg, "tzinfo", None) is not None and getattr(cmp_now, "tzinfo", None) is None:
            reg = reg.replace(tzinfo=None)
        elif getattr(reg, "tzinfo", None) is None and getattr(cmp_now, "tzinfo", None) is not None:
            cmp_now = cmp_now.replace(tzinfo=None)
        if (cmp_now - reg) < timedelta(hours=24):
            record_event(
                "delayed_activation",
                {
                    "user_id": user_id,
                    "registered_at": reg.isoformat(),
                    "device_fingerprint": device_fp,
                },
            )
            return True, "delayed_activation"

    # --- 6) 通过 ---------------------------------------------------------
    record_event("eligible", {"user_id": user_id, "device_fingerprint": device_fp})
    return True, "ok"


__all__ = [
    "TrialPurchaseRecord",
    "RiskEvent",
    "PurchaseRecordRepo",
    "InMemoryPurchaseRecordRepo",
    "ip_to_segment",
    "check_purchase_eligibility",
]
