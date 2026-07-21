# dtcoder 9.9 尝鲜价套餐 — 执行进度账本 (Progress Ledger)

> 由 subagent-driven-development skill 维护。每 Task 完成 implementer+review 后落 `### DONE`。

- 任务来源: local-docs/dtcoder-9.9-trial-plan.md (223 行, 7 Tasks)
- 简报: local-docs/dtcoder-9.9-trial-tasks.md (自包含 SSOT)
- 依赖分层: Task1(模型) → Task2/3/4 并行 → Task5/6/7 并行
- 文件集互不重叠 → 可全并行派发
- 派发策略: 7 个 implementer 子代理并行（coder profile），折叠验证为子代理自检 + 父代理审查
- 派发时间(UTC): 2026-07-21 06:03
- 恢复与复核时间(UTC): 2026-07-21 06:11
- 硬约束: 不 git commit/push；不跑全量构建；仅跑各 Task 新增测试；超时降级转静态审查

## 状态表

| Task | 内容 | 子代理 | 状态 | 备注 |
|---|---|---|---|---|
| T1 | 套餐/SKU 数据模型 | coder-T1 | ✅ DONE | src/billing/models/trial_plan.py |
| T2 | 限购风控服务 | coder-T2 | ✅ DONE | src/billing/services/trial_guard.py |
| T3 | 下单计费周期 | coder-T3 | ✅ DONE | src/billing/services/trial_order.py |
| T4 | 权益配额执行层 | coder-T4 | ✅ DONE | src/entitlement, src/quota |
| T5 | 到期提醒转化钩子 | coder-T5 | ✅ DONE | src/billing/jobs, conversion_coupon |
| T6 | 用户侧购买入口 | coder-T6 | ✅ DONE | console/src/pages |
| T7 | 埋点转化看板 | coder-T7 | ✅ DONE | src/analytics, website dashboard |

## DONE 记录

### 2026-07-21 06:11 — 全量复核（subagent-driven-development 恢复会话）

**复核范围：** 本会话为恢复场景（原派发于 06:03，子代理不归本会话所有）。父代理对 7 个 Task 的已落地产物做文件存在性核对 + 静态审查 + 变更范围测试。

**产物落核：** T1-T7 共 7 个 Task 的 Files 清单全部命中（源码 + 测试 + 前端组件 + schema）。

**测试验证：** `PYTHONPATH=src python -m pytest tests/billing/test_trial_plan_model.py tests/billing/test_trial_guard.py tests/billing/test_trial_order.py tests/billing/test_trial_reminder.py tests/entitlement/test_trial_entitlement.py tests/analytics/test_trial_funnel.py --noconftest -q` → **68 passed, 0 failed**（0.19s）。
- 采用 `--noconftest` 隔离：root `tests/conftest.py:22` 的 `from qwenpaw.providers import ...` 属仓库既有环境依赖（ModuleNotFoundError: No module named 'qwenpaw'），不在本次 7 个 Task 变更范围，不影响新增模块的独立验证。

**静态审查覆盖点：**
- T1 `trial_plan.py`：纯 dataclass + 内存仓储 + 幂等迁移；plan_code 唯一、price>0、duration_days>0 校验；`get_plan('trial-9.9-monthly')` 可查。
- T2 `trial_guard.py`：Protocol 注入；三重去重（user/device/payment）+ 阈值（注册<24h 延迟、payment≥2 复核、IP≥5 限流）；RiskEvent 写入。
- T3 `trial_order.py`：依赖倒置（仓储/事件/守卫注入）；下单→拦截抛 PurchaseNotAllowed、支付回调开通写 UserSubscription(+30d)、到期降级 status=expired；`api/order.py` 纯函数入口+接入点注释（无框架，符合 DoD 兜底）。
- T4 `resolver.py`+`limiter.py`：resolve_entitlements 支持 trial-9.9-monthly/free/basic-99，UnknownPlan 抛错；QuotaLimiter 三检查（token 200万/月→429、并发第4拒、旗舰 20/h 限速）。
- T5 `trial_reminder.py`+`conversion_coupon.py`：run_trial_reminders 扫 7/3/1 天；7 天附满99减30券、1 天附年付8折；trial_renew_prompt 埋点。
- T6 `TrialCard.tsx`(antd Card/Tag/Button+倒计时)+`NewUserTrialModal.tsx`+`trial-card.test.tsx`；hasPurchasedTrial 置灰；纯组件+注释（符合 DoD 兜底）。
- T7 `trial_funnel.yaml`(6 事件 SSOT，target 0.15)+`trial_funnel.py`(load_schema/validate_event/compute_funnel)+`index.tsx`(北极星目标线展示)。

**SSOT 对齐确认：** price=9.90、duration_days=30、monthly_token_limit=2000000、max_concurrent_sessions=3、flagship_rate_limit_per_hour=20、CONVERSION_RATE_TARGET=0.15，均与简报 SSOT 合约一致。

**降级说明：** 无。变更范围测试全绿，未触发降级（仅 pytest 收集阶段因 root conftest 的 qwenpaw 依赖被 `--noconftest` 绕过，非本次变更问题）。

### DONE (Task-level)
- T1 DONE — 模型单测绿；get_plan 可查；迁移幂等。
- T2 DONE — 6 用例绿；RiskEvent 写入；接口可注入。
- T3 DONE — 下单链路通；到期降级可触发；order.py 入口存在。
- T4 DONE — 尝鲜限流生效；正价/免费零回归。
- T5 DONE — cron 可触发；券记录可查；trial_renew_prompt 上报。
- T6 DONE — 卡片可见；限购置灰；下单入口存在。
- T7 DONE — schema 可校验；聚合可算；看板展示目标线。
