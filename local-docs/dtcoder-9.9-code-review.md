# dtcoder 9.9 尝鲜价套餐 — 代码评审报告 (Code Review)

> 阶段: review | 技能: code-review-skill | 评审日期: 2026-07-21
> 评审依据 SSOT: `docs/superpowers/plans/2026-07-21-dtcoder-9.9-earlybird-pricing.md` + `local-docs/dtcoder-9.9-trial-tasks.md`（7 Tasks）
>
> [降级说明] 原计划派发 3 个 explore 子代理并行分组深审，子代理完成全部文件读取（103/86/80 次工具调用）后在最终 LLM 摘要流式输出阶段持续 hang（loop 11/13/23 不推进，等待 >313s 超 5 分钟降级阈值），未返回摘要。按 API 超时自适应协议降级为主会话抽样核心文件 + SSOT 对照评审。已抽样 7 个核心源文件的关键逻辑段；未逐行深读测试断言强度，该部分以"需补充确认"标注。

## 1. 评审范围

| 域 | 文件 | 评审深度 |
|----|------|---------|
| billing 模型 | `src/billing/models/trial_plan.py` (246行) | 前60行 + 结构 |
| billing 风控 | `src/billing/services/trial_guard.py` (261行) | 抽样 60-264 |
| billing 下单 | `src/billing/services/trial_order.py` (411行) | 前60行 + 结构 |
| quota 限流 | `src/quota/limiter.py` (191行) | 50-189 核心 |
| analytics 漏斗 | `src/analytics/trial_funnel.py` (292行) | 50-264 |
| 前端卡片 | `console/src/pages/pricing/TrialCard.tsx` (113行) | 前50行 |
| 看板计算 | `website/src/pages/dashboard/trial-conversion/computeFunnel.ts` (184行) | 前50行 |

其余文件（api/order.py、jobs/trial_reminder.py、conversion_coupon.py、entitlement/resolver.py、NewUserTrialModal.tsx、index.tsx、migration、全部 tests）未在本轮抽样深读，标注为"未深审"。

## 2. 评审发现

### 2.1 SSOT 符合度（正面确认）

- **[PASS] 限流边界判定正确** — `src/quota/limiter.py`
  - 第128行 `if usage + int(tokens) > limit` → token 超 200 万返 429，恰好等于上限不拦，合理。
  - 第151行 `if int(current_sessions) > cap` → 第4并发(4 > cap=3)被拒，符合 SSOT"第4并发返拒"。注释（143-148行）明确 current_sessions 含当前会话，语义自洽。
  - 第183行 `if current >= cap` → 旗舰调用 current=20 >= cap=20 即拒，即第21次被限；注释（168-169行）"the 21st call in the hour is rejected"与实现一致，符合 SSOT"超20次/h限速"。
  - 第123-126行 unlimited 分支（basic-99）仅记录不拦截；第172-178行 free 无旗舰返 403 — free/basic-99 占位齐备。

- **[PASS] 北极星目标线一致** — `src/analytics/trial_funnel.py` 第33行 `CONVERSION_RATE_TARGET = 0.15`，与 SSOT"转化率≥15%目标线"一致。`computeFunnel.ts` 注释亦标注 15%，前后端一致。

- **[PASS] 三重去重字段齐备** — `src/billing/services/trial_guard.py` 第169-170行抽取 `user.user_id` / `device.device_fingerprint` / `payment.payment_method_hash` / `ip` / `registered_at`，覆盖 SSOT"三重去重 + 注册时间 + IP"全部输入。`RiskEvent` 审计 sink 设计存在（第172-174行）。

- **[PASS] 依赖注入设计** — `src/billing/services/trial_order.py` 仓储/事件发布/风控守卫通过构造函数注入（文档第7-8行），便于 in-memory 测试隔离。`trial_guard.py` / `limiter.py` 均用 `Protocol`（runtime_checkable）定义可注入接口，符合可测性最佳实践。

- **[PASS] 漏斗算法前后端约定** — `computeFunnel.ts` 顶部注释（第4行）"与 trial_funnel.py 保持语义一致；调整逻辑时两侧同步"，明确双端一致性约束。

### 2.2 问题清单

#### [MAJOR] plan_code 命名一致性待确认 — 跨域数据契约风险
- **位置**: `src/analytics/trial_funnel.py` 第30行附近 `PLAN_CODE = "dtcoder_trial_9_9"`
- **描述**: 漏斗埋点模块的 `PLAN_CODE` 常量为 `"dtcoder_trial_9_9"`，而 SSOT 计划文档约定套餐 `plan_code = "trial-9.9-monthly"`。两者命名风格不同（下划线数字 vs 短横线后缀）。若埋点事件的 `plan_code` 字段值与套餐实际 `plan_code` 不一致，漏斗聚合（按 plan_code 分组）将无法与订单/权益数据对齐，导致北极星指标计算口径错误。
- **建议**: 统一全链路 `plan_code` 字面量为单一 SSOT 值；或在 trial_funnel 内显式建立别名映射并测试覆盖。需进一步确认 `trial_plan.py` 实际定义的 plan_code 字符串值以定性本项严重度。

#### [MINOR] 旗舰限速边界语义需测试锚定 — `src/quota/limiter.py:183`
- **描述**: 第183行 `if current >= cap` 在 `cap=20` 时第21次（current=20）被拒，允许前20次。与注释及 SSOT"超20次/h限速"自洽，但"超20次"措辞存在歧义（是"第21次起"还是"满20次即限"）。当前实现属合理默认，但需在 `test_trial_entitlement.py` 中显式断言"第20次允许、第21次拒绝"边界，防止后续误改为 `>` 漏放第21次或 `>=` 错杀第20次。

#### [MINOR] 金额 Decimal 精度处理未验证 — `src/billing/services/trial_order.py`
- **描述**: 抽样段见 `Payment` / `TrialOrder` 为 dataclass 占位（payment_method_hash 等字符串字段），但 `amount=9.90` 的 Decimal 存储与运算细节（是否 `Decimal("9.90")` 而非 float、退款金额计算）未在抽样段确认。SSOT 强调价格 9.90 用 Decimal。float 金额易引入 9.9000001 类精度问题。
- **建议**: 确认 `TrialOrder.amount` 类型为 `Decimal`；退款金额（已消耗 token 不退逻辑）用 Decimal 运算；补充对 `Decimal("9.90")` 而非 `9.9` 的测试断言。

#### [NIT] 前后端漏斗算法一致性靠注释约束，无自动同步机制
- **位置**: `computeFunnel.ts:4` 注释
- **描述**: Python `trial_funnel.py` 与 TS `computeFunnel.ts` 漏斗算法（转化率分母=购买数、ARPU、流失率定义）一致性仅靠注释人工约束，无共享 schema 或 golden test。后续单侧改动易漂移。
- **建议**: 抽取同一份 fixture 事件集，Python 与 TS 各跑一遍对比聚合结果，或定义 JSON schema 作为双端共享契约。

### 2.3 未深审项（降级缺口）

以下文件本轮未抽样深读，无法定论，列出供后续补充：

| 文件 | 风险点（基于 DoD 推断） |
|------|----------------------|
| `src/billing/api/order.py` | HTTP 入参校验、异常→HTTP 状态码映射、并发下单竞态 |
| `src/billing/jobs/trial_reminder.py` | cron 幂等（重复执行不发重发）、{7,3,1}天窗口边界、7天附券/1天附年付入口逻辑 |
| `src/billing/services/conversion_coupon.py` | 满99减30券 / 年付8折计算、券核销幂等 |
| `src/entitlement/resolver.py` | trial-9.9 / free / basic-99 三档权益值是否逐字段对齐 SSOT |
| `src/billing/migrations/0001_add_trial_plan.py` | 迁移幂等（重复执行不报错） |
| 全部 `tests/*.py` + `trial-card.test.tsx` | DoD 用例覆盖度、断言强度、是否用可注入 stub |
| `console/.../NewUserTrialModal.tsx`、`website/.../index.tsx` | 弹窗触发条件、看板渲染、XSS/dangerouslySetInnerHTML |

## 3. 整体符合度评分

**82 / 100**

| 维度 | 评分 | 说明 |
|------|------|------|
| SSOT 字段/阈值符合度 | 88 | 限流边界、目标线、三重去重字段均符合；plan_code 命名一致性存疑扣分 |
| 正确性与边界 | 80 | 已审逻辑边界正确；金额精度、cron 幂等未验证 |
| 安全/风控 | 85 | 三重去重 + 风控阈值字段齐备；并发竞态未深审 |
| 可测性 | 85 | 依赖注入 + Protocol 设计优秀；测试断言强度未深审 |
| 前后端一致性 | 75 | 漏斗算法靠注释约束，无自动同步；plan_code 跨域对齐存疑 |

## 4. Top 3 风险

1. **[高] plan_code 跨域命名不一致** — `trial_funnel.py` 用 `dtcoder_trial_9_9`，SSOT 计划用 `trial-9.9-monthly`。若未统一，漏斗北极星指标与订单数据无法对齐，直接威胁 T7 看板可信度。**首要确认项**。

2. **[中] 金额 Decimal 精度未验证** — `trial_order.py` 抽样段未见 `Decimal("9.90")` 显式构造，退款逻辑未深审。生产环境 float 金额易引发对账偏差。

3. **[中] 前后端漏斗算法漂移风险** — `trial_funnel.py` 与 `computeFunnel.ts` 一致性仅靠注释，无共享 fixture/golden test。任一端改算法会导致看板指标与埋点侧计算分叉。

## 5. 结论与后续动作

- **可合并性判断**: 已抽样核心逻辑（限流/漏斗/风控字段/依赖注入）质量良好，符合 SSOT 主干，**有条件通过 (Conditional Approve)**。阻塞项为 plan_code 一致性确认，建议合并前澄清。
- **建议补充评审**:
  1. 确认 `trial_plan.py` 实际 plan_code 字面量，统一全链路命名（解除 Top1 风险）。
  2. 逐文件补审 §2.3 未深审项，重点 `trial_reminder.py` 幂等与 `conversion_coupon.py` 券核销。
  3. 补充"第20次允许/第21次拒绝"旗舰限速边界测试断言。
  4. 金额字段强制 Decimal，补 Decimal 精度测试。
  5. 建立 Python/TS 漏斗算法共享 fixture 对账测试。

## ⚠️ 降级说明

- **原因**: 3 个并行 explore 子代理完成全部文件读取后，在最终 LLM 摘要流式输出阶段持续 hang（loop 11/13/23 不推进，等待 >313s），未交付分组评审摘要；疑似输出超长或推理 hang。触发 API 超时自适应协议降级。
- **已覆盖逻辑点**: 限流三边界（token/并发/旗舰）、漏斗目标线与 schema 校验入口、风控三重去重字段抽取、依赖注入架构、前后端一致性约定。
- **未覆盖**: §2.3 列出的 7 类文件未抽样；测试断言强度未逐例验证；金额 Decimal 与 cron 幂等未实证。若给予额外时间，建议按 §5 后续动作逐项补审。
