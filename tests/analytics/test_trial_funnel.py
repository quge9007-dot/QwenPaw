# -*- coding: utf-8 -*-
"""Task 7 — 转化漏斗埋点 TDD 测试。

覆盖两个核心用例：
  1. test_event_schema_validation_* ：事件 schema 校验
     （必填字段缺失 / 类型错误 / 未知事件类型 抛错；合法事件通过）。
  2. test_compute_funnel_aggregation_* ：漏斗聚合计算正确
     （给定事件序列得正确转化率 / ARPU / 流失率 / 触点贡献 / 北极星）。

运行（仓库标准方式）：
    python -m pytest tests/analytics/test_trial_funnel.py -q

说明：本测试仅依赖 PyYAML（pyproject.toml 已声明）与 pytest。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让测试在未做 editable install 的环境（src 不在 sys.path）下也能直接导入。
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest  # noqa: E402

from analytics.trial_funnel import (  # noqa: E402
    CONVERSION_RATE_TARGET,
    EventValidationError,
    compute_funnel,
    load_schema,
    validate_event,
)


# ---- 固定数据 -----------------------------------------------------------------

PLAN = "dtcoder_trial_9_9"
TS = "2026-07-21T06:00:00Z"


def _ev(event: str, user_id: str = "u1", value=None, **extra) -> dict:
    """构造一个合法事件（除显式删除字段外）。"""
    ev = {"event": event, "user_id": user_id, "plan_code": PLAN, "ts": TS}
    if value is not None:
        ev["value"] = value
    ev.update(extra)
    return ev


# ===========================================================================
# 用例 1：事件 schema 校验
# ===========================================================================
class TestEventSchemaValidation:
    """必填字段缺失抛错；类型 / 约束错误抛错；合法事件通过。"""

    def test_valid_event_passes(self) -> None:
        schema = load_schema()
        validate_event(_ev("view"), schema)
        validate_event(_ev("purchase", value=9.9), schema)
        validate_event(_ev("convert_to_paid", value=99.0), schema)

    def test_missing_required_field_raises(self) -> None:
        schema = load_schema()
        # 缺 user_id
        bad = {"event": "view", "plan_code": PLAN, "ts": TS}
        with pytest.raises(EventValidationError):
            validate_event(bad, schema)
        # 缺 ts
        bad = {"event": "purchase", "user_id": "u1", "plan_code": PLAN}
        with pytest.raises(EventValidationError):
            validate_event(bad, schema)
        # 缺 plan_code
        bad = {"event": "activate", "user_id": "u1", "ts": TS}
        with pytest.raises(EventValidationError):
            validate_event(bad, schema)

    def test_required_field_empty_raises(self) -> None:
        schema = load_schema()
        with pytest.raises(EventValidationError):
            validate_event({"event": "view", "user_id": "", "plan_code": PLAN, "ts": TS}, schema)
        with pytest.raises(EventValidationError):
            validate_event({"event": "view", "user_id": "u1", "plan_code": PLAN, "ts": ""}, schema)

    def test_unknown_event_type_raises(self) -> None:
        schema = load_schema()
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "bogus", "user_id": "u1", "plan_code": PLAN, "ts": TS},
                schema,
            )

    def test_wrong_plan_code_raises(self) -> None:
        schema = load_schema()
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "view", "user_id": "u1", "plan_code": "wrong_plan", "ts": TS},
                schema,
            )

    def test_bad_value_type_raises(self) -> None:
        schema = load_schema()
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "purchase", "user_id": "u1", "plan_code": PLAN, "ts": TS, "value": "not-a-number"},
                schema,
            )
        # 负值
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "purchase", "user_id": "u1", "plan_code": PLAN, "ts": TS, "value": -1},
                schema,
            )
        # bool 不被当作数值
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "purchase", "user_id": "u1", "plan_code": PLAN, "ts": TS, "value": True},
                schema,
            )

    def test_bad_ts_raises(self) -> None:
        schema = load_schema()
        with pytest.raises(EventValidationError):
            validate_event(
                {"event": "view", "user_id": "u1", "plan_code": PLAN, "ts": "not-a-date"},
                schema,
            )


# ===========================================================================
# 用例 2：漏斗聚合计算
# ===========================================================================
class TestComputeFunnelAggregation:
    """给定事件序列得正确转化率 / ARPU / 流失率 / 触点贡献 / 北极星。"""

    @staticmethod
    def _sample_events() -> list[dict]:
        # 3 名用户：u1 转化、u2 流失、u3 仅浏览未购买。
        return [
            _ev("view", "u1"),
            _ev("view", "u2"),
            _ev("view", "u3"),
            _ev("purchase", "u1", value=9.9),
            _ev("purchase", "u2", value=9.9),
            _ev("activate", "u1"),
            _ev("activate", "u2"),
            _ev("renew_prompt", "u1"),
            _ev("renew_prompt", "u2"),
            _ev("convert_to_paid", "u1", value=99.0),  # 正价订阅
            _ev("churn", "u2"),
        ]

    def test_stage_counts_and_populations(self) -> None:
        r = compute_funnel(self._sample_events())
        assert r["stage_counts"] == {
            "view": 3,
            "purchase": 2,
            "activate": 2,
            "renew_prompt": 2,
            "convert_to_paid": 1,
            "churn": 1,
        }
        assert r["unique_users"] == 3
        assert r["purchasers"] == 2
        assert r["converts"] == 1
        assert r["churns"] == 1

    def test_conversion_rate_and_north_star(self) -> None:
        r = compute_funnel(self._sample_events())
        # converts=1, purchasers=2 -> 0.5，超过 15% 目标线
        assert r["conversion_rate"] == pytest.approx(0.5)
        assert r["north_star"]["metric"] == "conversion_rate"
        assert r["north_star"]["target"] == CONVERSION_RATE_TARGET
        assert r["north_star"]["value"] == pytest.approx(0.5)
        assert r["north_star"]["meets_target"] is True

    def test_arpu_and_revenue(self) -> None:
        r = compute_funnel(self._sample_events())
        # ARPU = sum(convert_to_paid.value=99.0) / purchasers=2 = 49.5
        assert r["total_revenue"] == pytest.approx(99.0)
        assert r["arpu"] == pytest.approx(49.5)

    def test_churn_rate(self) -> None:
        r = compute_funnel(self._sample_events())
        # churns=1, purchasers=2 -> 0.5
        assert r["churn_rate"] == pytest.approx(0.5)

    def test_touchpoint_contribution(self) -> None:
        r = compute_funnel(self._sample_events())
        tc = r["touchpoint_contribution"]
        # converted = {u1}；u1 经历过 view/purchase/activate/renew_prompt
        assert tc["view"] == pytest.approx(1.0)
        assert tc["purchase"] == pytest.approx(1.0)
        assert tc["activate"] == pytest.approx(1.0)
        assert tc["renew_prompt"] == pytest.approx(1.0)

    def test_below_target_when_no_converts(self) -> None:
        events = [
            _ev("view", "u1"),
            _ev("view", "u2"),
            _ev("purchase", "u1", value=9.9),
            _ev("purchase", "u2", value=9.9),
            _ev("activate", "u1"),
            _ev("renew_prompt", "u1"),
            _ev("churn", "u1"),
            _ev("churn", "u2"),
        ]
        r = compute_funnel(events)
        # converts=0, purchasers=2 -> 0.0，未达 15% 目标
        assert r["conversion_rate"] == 0.0
        assert r["north_star"]["meets_target"] is False
        assert r["arpu"] == 0.0
        assert r["churn_rate"] == pytest.approx(1.0)

    def test_invalid_event_propagates(self) -> None:
        # 混入一条非法事件（缺 ts），compute_funnel 应抛错而非静默
        events = self._sample_events() + [{"event": "view", "user_id": "u4", "plan_code": PLAN}]
        with pytest.raises(EventValidationError):
            compute_funnel(events)
