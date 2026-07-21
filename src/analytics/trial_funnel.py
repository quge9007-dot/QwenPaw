# -*- coding: utf-8 -*-
"""
dtcoder 9.9 尝鲜价套餐 — 转化漏斗埋点：schema 加载 / 事件校验 / 漏斗聚合。

本模块是 Task 7（埋点与转化数据看板）的 Python 计算核心：
  * ``load_schema``        读取并解析 ``events/trial_funnel.yaml``（SSOT）。
  * ``validate_event``     按校验单条事件：必填字段、字段类型与约束。
  * ``compute_funnel``     聚合一组事件，输出各阶段数、转化率、ARPU、流失率、
                           各触点贡献及北极星指标（转化率 vs 15% 目标线）。

看板侧（website/src/pages/dashboard/trial-conversion/）的 TypeScript 计算函数
``computeFunnel.ts`` 与本实现保持语义一致；如需调整，两侧同步修改。

仓库约定：Python 工程，src/ 平铺布局，pytest 测试镜像 src/ 结构。
依赖：PyYAML（已在 pyproject.toml 中声明）。
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

# ---- 常量（与 yaml schema 对应；模块级暴露便于看板 / 测试引用）-------------------

#: 漏斗阶段（生命周期顺序）
EVENT_TYPES: tuple[str, ...] = (
    "view",
    "purchase",
    "activate",
    "renew_prompt",
    "convert_to_paid",
    "churn",
)

#: 所有事件共享的必填字段
REQUIRED_FIELDS: tuple[str, ...] = ("user_id", "plan_code", "ts")

#: 可选字段
OPTIONAL_FIELDS: tuple[str, ...] = ("value",)

#: 套餐编码
PLAN_CODE = "dtcoder_trial_9_9"

#: 北极星转化率目标线
CONVERSION_RATE_TARGET = 0.15

#: schema 文件位置（相对本模块）
_SCHEMA_PATH = Path(__file__).resolve().parent / "events" / "trial_funnel.yaml"


class EventValidationError(ValueError):
    """事件违反 trial_funnel schema 时抛出。"""


# ---- schema 加载 ----------------------------------------------------------------

def load_schema(path: str | Path | None = None) -> dict[str, Any]:
    """加载并返回 trial_funnel.yaml 的 schema 字典。

    Args:
        path: 自定义 schema 路径；缺省使用模块旁的 events/trial_funnel.yaml。

    Returns:
        解析后的 schema dict（结构见 yaml 顶部注释）。
    """
    p = Path(path) if path else _SCHEMA_PATH
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, Mapping):
        raise EventValidationError(f"schema root must be a mapping, got {type(data).__name__}")
    return dict(data)


# ---- 字段类型校验辅助 -----------------------------------------------------------

#: schema 字段类型 -> Python 校验
_TYPE_CHECKERS: dict[str, tuple[type, ...]] = {
    "str": (str,),
    "float": (int, float),  # 整数也接受为数值
    "datetime": (str,),
    "int": (int,),
}

#: bool 在 Python 里是 int 子类，金额字段不应接受 True/False
def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _parse_ts(ts: Any) -> None:
    """轻量 ISO-8601 校验：必须是字符串且可被 datetime.fromisoformat 解析（兼容 Z）。"""
    if not isinstance(ts, str):
        raise EventValidationError(f"ts must be ISO-8601 string, got {type(ts).__name__}")
    candidate = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    try:
        _dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise EventValidationError(f"ts must be valid ISO-8601, got {ts!r}: {exc}") from exc


# ---- 事件校验 ------------------------------------------------------------------

def validate_event(
    event: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> None:
    """按 schema 校验单条事件，违反时抛出 :class:`EventValidationError`。

    校验项：
      1. event 必须是 mapping；
      2. ``event`` 字段必须为 schema 中已定义的事件类型；
      3. 该事件 required 字段必须存在且非空；
      4. 共享字段类型 / 约束：
         - user_id: 非空 str
         - plan_code: 必须等于 PLAN_CODE
         - ts: ISO-8601 字符串
         - value: 若存在必须是数值且 >= 0
    """
    if schema is None:
        schema = load_schema()

    if not isinstance(event, Mapping):
        raise EventValidationError(
            f"event must be a mapping, got {type(event).__name__}"
        )

    ev_type = event.get("event")
    events_def = schema.get("events", {})
    if ev_type not in events_def:
        raise EventValidationError(
            f"unknown event type: {ev_type!r}; expected one of {list(events_def)}"
        )
    ev_def = events_def[ev_type] or {}

    # 必填字段存在性（同时排除 None / 空串）
    for field in ev_def.get("required", REQUIRED_FIELDS):
        if field not in event:
            raise EventValidationError(
                f"event {ev_type!r} missing required field {field!r}"
            )
        val = event.get(field)
        if val is None or (isinstance(val, str) and val == ""):
            raise EventValidationError(
                f"event {ev_type!r} required field {field!r} must be non-empty"
            )

    fields_def = schema.get("fields", {}) or {}

    # user_id
    uid = event.get("user_id")
    if "user_id" in fields_def and uid is not None:
        if not isinstance(uid, str):
            raise EventValidationError(
                f"user_id must be str, got {type(uid).__name__}"
            )

    # plan_code
    pc = event.get("plan_code")
    if "plan_code" in fields_def and pc is not None:
        if pc != PLAN_CODE:
            raise EventValidationError(
                f"plan_code must be {PLAN_CODE!r}, got {pc!r}"
            )

    # ts
    if "ts" in fields_def and event.get("ts") is not None:
        _parse_ts(event["ts"])

    # value（可选）
    if "value" in event and event["value"] is not None:
        v = event["value"]
        if not _is_number(v):
            raise EventValidationError(
                f"value must be a number, got {type(v).__name__}"
            )
        if v < 0:
            raise EventValidationError(f"value must be >= 0, got {v}")


def validate_events(events: Iterable[Mapping[str, Any]], schema: Mapping[str, Any] | None = None) -> None:
    """校验事件序列；任一失败即抛出（首次失败处）。"""
    for idx, ev in enumerate(events):
        try:
            validate_event(ev, schema)
        except EventValidationError as exc:
            raise EventValidationError(f"events[{idx}] invalid: {exc}") from exc


# ---- 漏斗聚合 ------------------------------------------------------------------

def compute_funnel(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """聚合事件序列，输出漏斗指标。

    指标定义：
      * stage_counts: 各阶段事件次数（按 event 计数，含重复触达）。
      * unique_users: 去重用户数（任意事件）。
      * purchasers: 至少发生过一次 purchase 的去重用户数。
      * converts:   发生过 convert_to_paid 的去重用户数。
      * churns:     发生过 churn 的去重用户数。
      * conversion_rate: 北极星指标 = converts / purchasers（无购买者时为 0）。
      * churn_rate:       churns / purchasers（无购买者时为 0）。
      * arpu:             sum(convert_to_paid.value) / purchasers（无购买者时为 0）。
      * total_revenue:    sum(convert_to_paid.value)。
      * touchpoint_contribution: 每个触点对转化的归因贡献
        = |converted ∩ touched| / |converted|（无转化时为 0）。
      * north_star: {metric, target, value, meets_target}。

    所有事件会先经 :func:`validate_event` 校验；任一非法即抛错。
    """
    schema = load_schema()
    validate_events(events, schema)

    counts: dict[str, int] = {stage: 0 for stage in EVENT_TYPES}
    users: set[str] = set()
    purchasers: set[str] = set()
    activated: set[str] = set()
    renew_prompted: set[str] = set()
    converted: set[str] = set()
    churned: set[str] = set()
    total_revenue = 0.0

    for ev in events:
        et = ev["event"]
        counts[et] += 1
        uid = ev["user_id"]
        users.add(uid)
        if et == "purchase":
            purchasers.add(uid)
        elif et == "activate":
            activated.add(uid)
        elif et == "renew_prompt":
            renew_prompted.add(uid)
        elif et == "convert_to_paid":
            converted.add(uid)
            total_revenue += float(ev.get("value") or 0.0)
        elif et == "churn":
            churned.add(uid)

    purchaser_n = len(purchasers)
    convert_n = len(converted)
    churn_n = len(churned)

    conversion_rate = convert_n / purchaser_n if purchaser_n else 0.0
    churn_rate = churn_n / purchaser_n if purchaser_n else 0.0
    arpu = total_revenue / purchaser_n if purchaser_n else 0.0

    touchpoint_contribution: dict[str, float] = {}
    touchpoint_sets = {
        "view": users,
        "purchase": purchasers,
        "activate": activated,
        "renew_prompt": renew_prompted,
    }
    for tp, tp_set in touchpoint_sets.items():
        touchpoint_contribution[tp] = (
            len(converted & tp_set) / convert_n if convert_n else 0.0
        )

    return {
        "stage_counts": counts,
        "unique_users": len(users),
        "purchasers": purchaser_n,
        "converts": convert_n,
        "churns": churn_n,
        "conversion_rate": conversion_rate,
        "churn_rate": churn_rate,
        "arpu": round(arpu, 6),
        "total_revenue": round(total_revenue, 6),
        "touchpoint_contribution": touchpoint_contribution,
        "north_star": {
            "metric": "conversion_rate",
            "target": CONVERSION_RATE_TARGET,
            "value": conversion_rate,
            "meets_target": conversion_rate >= CONVERSION_RATE_TARGET,
        },
    }


__all__ = [
    "EVENT_TYPES",
    "REQUIRED_FIELDS",
    "OPTIONAL_FIELDS",
    "PLAN_CODE",
    "CONVERSION_RATE_TARGET",
    "EventValidationError",
    "load_schema",
    "validate_event",
    "validate_events",
    "compute_funnel",
]
