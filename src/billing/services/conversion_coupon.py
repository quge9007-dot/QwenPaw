"""转化券服务 — dtcoder 9.9 尝鲜价套餐 Task 5.

提供 ``issue_conversion_coupon``，按 SSOT 合约写 ``Coupon`` 记录，用于到期提醒的转化钩子：

* ``discount_full``  — 正价满减券（满 99 减 30），第 1 次（7 天）提醒附送。
* ``annual_discount`` — 年付 8 折入口，第 3 次（1 天）提醒附送。

设计为纯函数 + 可注入仓储，无 ORM 框架时也能在内存仓储上独立运行（见 SSOT 仓库约定）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable


# 合约常量（来自 SSOT） -------------------------------------------------------
COUPON_TYPE_DISCOUNT_FULL = "discount_full"
COUPON_TYPE_ANNUAL_DISCOUNT = "annual_discount"
VALID_COUPON_TYPES = {COUPON_TYPE_DISCOUNT_FULL, COUPON_TYPE_ANNUAL_DISCOUNT}

# 满 99 减 30
DISCOUNT_FULL_VALUE = Decimal("30")
DISCOUNT_FULL_MIN_SPEND = Decimal("99")
# 年付 8 折 → 折扣比例 0.2（即减免 20%）
ANNUAL_DISCOUNT_VALUE = Decimal("0.2")

# 券默认有效期：满减券 7 天，年付折扣券 3 天（到期前 1 天发放，覆盖剩余转化窗口）
DEFAULT_TTL = {
    COUPON_TYPE_DISCOUNT_FULL: timedelta(days=7),
    COUPON_TYPE_ANNUAL_DISCOUNT: timedelta(days=3),
}


@dataclass
class Coupon:
    """转化券记录。

    字段对齐 SSOT：``id / user_id / type / value / min_spend / expires_at / status``。
    """

    id: str
    user_id: str
    type: str
    value: Decimal
    min_spend: Decimal | None = None
    expires_at: datetime | None = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_active(self, now: datetime | None = None) -> bool:
        if self.status != "active":
            return False
        if self.expires_at is not None and (now or datetime.utcnow()) >= self.expires_at:
            return False
        return True


@runtime_checkable
class CouponRepo(Protocol):
    """券仓储协议（可注入 in-memory 实现）。"""

    def save(self, coupon: Coupon) -> Coupon:  # pragma: no cover - protocol
        ...


def _next_id() -> str:
    import uuid

    return f"cpn_{uuid.uuid4().hex}"


def issue_conversion_coupon(
    user: Any,
    coupon_type: str,
    value: Decimal | None = None,
    coupon_repo: CouponRepo | None = None,
    *,
    now: datetime | None = None,
    min_spend: Decimal | None = None,
    expires_at: datetime | None = None,
) -> Coupon:
    """写一张转化券 ``Coupon`` 记录并返回。

    :param user: 任意带 ``user_id`` 属性的对象（或 str user_id）。
    :param coupon_type: ``discount_full`` / ``annual_discount``。
    :param value: 券面值；为 None 时按 coupon_type 取 SSOT 默认值
       （满 99 减 30 → 30；年付 8 折 → 0.2）。
    :param coupon_repo: 可注入仓储；不传则只构造对象（用于测试捕获）。
    :param now: 当前时间，用于推算 ``expires_at``。
    :param min_spend: 最低消费门槛；None 时按 coupon_type 取默认。
    :param expires_at: 显式到期时间；None 时按 coupon_type 默认 TTL 推算。
    :return: 已写入的 ``Coupon``（status='active'）。
    :raises ValueError: coupon_type 非法。
    """
    if coupon_type not in VALID_COUPON_TYPES:
        raise ValueError(
            f"unknown coupon_type: {coupon_type!r}, "
            f"expected one of {sorted(VALID_COUPON_TYPES)}"
        )

    user_id = user if isinstance(user, str) else getattr(user, "user_id")
    if user_id is None:
        raise ValueError("cannot resolve user_id from user object")

    if value is None:
        value = (
            DISCOUNT_FULL_VALUE
            if coupon_type == COUPON_TYPE_DISCOUNT_FULL
            else ANNUAL_DISCOUNT_VALUE
        )
    value = Decimal(value)

    if min_spend is None:
        min_spend = (
            DISCOUNT_FULL_MIN_SPEND
            if coupon_type == COUPON_TYPE_DISCOUNT_FULL
            else None
        )
    if min_spend is not None:
        min_spend = Decimal(min_spend)

    moment = now or datetime.utcnow()
    if expires_at is None:
        expires_at = moment + DEFAULT_TTL[coupon_type]

    coupon = Coupon(
        id=_next_id(),
        user_id=str(user_id),
        type=coupon_type,
        value=value,
        min_spend=min_spend,
        expires_at=expires_at,
        status="active",
        created_at=moment,
    )

    if coupon_repo is not None:
        coupon_repo.save(coupon)

    return coupon
