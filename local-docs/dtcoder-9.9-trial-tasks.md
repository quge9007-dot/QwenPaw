# dtcoder 9.9 尝鲜价套餐 — 子代理任务简报（自包含 SSOT）

> 本文件供并行 implementer 子代理读取。每个 Task 一节，内含 Files / Steps / DoD 及全部 SSOT 合约，子代理无需再读 223 行原计划。
> 仓库约定：Python 工程，`src/` 平铺布局，`pyproject.toml` 管理依赖，测试放 `tests/` 镜像 `src/` 结构，用 `pytest`。
> 硬约束：仅创建/修改本 Task 列出的文件；仅对你新增的测试文件跑 `pytest`；禁止全量构建/全量回归；若某 `Update` 目标文件不存在，按合理结构创建并注明。

---

## SSOT 合约（所有 Task 共享）

### 套餐定义
| 字段 | 值 |
|---|---|
| plan_code | `trial-9.9-monthly` |
| 名称 | dtcoder 尝鲜版（首月） |
| price | 9.90（Decimal，分=990） |
| duration_days | 30 |
| 原价锚点 | 99.00 |
| purchase_limit | 1（每自然用户） |
| auto_renew | False（到期降级免费版） |

### 权益矩阵（entitlements JSON）
```json
{
  "monthly_token_limit": 2000000,
  "max_concurrent_sessions": 3,
  "context_window": 131072,
  "model_tier": ["base", "flagship"],
  "flagship_rate_limit_per_hour": 20,
  "advanced_skills": true,
  "priority_support": true,
  "history_retention_days": 90
}
```
对照：免费版 monthly_token=500000/并发1/32K/仅 base/历史7天；正价基础版 99 无限 token/并发5/200K/全模型。

### 限购风控（三重去重 + 阈值）
- 维度：user_id / device_fingerprint / payment_method_hash，任一命中历史已购即拦截。
- 阈值：同一 payment_method_hash 绑定 ≥2 不同 user_id → 人工复核；同 IP 段 24h 成交 ≥5 → 限流+告警；user 注册 <24h 购买 → 延迟 1h 到账 + 设备校验。
- 退款：已消耗 token 不退；未使用 7 天内可退。

### 转化漏斗埋点事件
`trial_view` / `trial_purchase` / `trial_activate` / `trial_renew_prompt` / `trial_convert_to_paid` / `trial_churn`。

### 生命周期
注册 → 引导 → 购买 9.9 → 到账开通 30 天 → 到期前 7/3/1 天提醒 → 升级正价(满 99 减 30 券) / 年付 8 折 / 流失降级。

---

## Task 1: 套餐与 SKU 配置数据模型
**Files:** Create `src/billing/models/trial_plan.py`, Create `tests/billing/test_trial_plan_model.py`, Create `src/billing/migrations/0001_add_trial_plan.py`
**Steps:**
1. 定义 `TrialPlan`（plan_code 唯一、price: Decimal>0、duration_days: int>0、entitlements: dict/JSON、quota_limits: dict/JSON、purchase_limit: int=1、is_active: bool=True）。提供 `get_plan(plan_code)` 类方法/函数返回 active 套餐。
2. 定义 `TrialPurchaseRecord`（user_id、device_fingerprint、payment_method_hash、purchased_at、status）。
3. 迁移脚本：插入 `trial-9.9-monthly` 默认配置（price=9.90、duration_days=30、entitlements 见 SSOT、purchase_limit=1、is_active=True）。
4. TDD：先写测试（限购=1、price>0、duration_days>0、`get_plan('trial-9.9-monthly')` 返回正确套餐、重复 plan_code 唯一约束），再实现。无 ORM 框架则用纯 dataclass + 内存仓储 + 迁移函数（idempotent），保证测试可独立运行。
**DoD:** 模型单测绿；`get_plan('trial-9.9-monthly')` 可查询到；迁移幂等。

## Task 2: 限购与风控校验服务
**Files:** Create `src/billing/services/trial_guard.py`, Create `tests/billing/test_trial_guard.py`
**Steps:**
1. `check_purchase_eligibility(user, device, payment) -> (allowed: bool, reason: str)`。user 含 user_id/registered_at/ip；device 含 device_fingerprint；payment 含 payment_method_hash。
2. 三重去重：查 `TrialPurchaseRecord` 中 user_id / device_fingerprint / payment_method_hash 任一命中 → (False, "duplicate_*")。
3. 风控阈值：注册<24h → 标记 delayed_activation=True（不拦截但延迟）；payment 绑定≥2 账号 → (False, "manual_review")；同 IP 段 24h≥5 单 → (False, "ip_throttle")。记录 `RiskEvent`（含 event_type, payload, created_at）。
4. TDD 6 用例：首次可购、重复账号拦截、重复设备拦截、重复支付拦截、新注册延迟标记、IP 限流拦截。仓储用可注入的 in-memory repo 以便测试。
**DoD:** 6 用例全绿；RiskEvent 写入；接口可被下单服务注入。

## Task 3: 下单与计费周期服务
**Files:** Create `src/billing/services/trial_order.py`, Update `src/billing/api/order.py`（不存在则创建）, Create `tests/billing/test_trial_order.py`
**Steps:**
1. `create_trial_order(user, plan_code, payment_channel)`：调 Task2 guard → 命中拦截抛 `PurchaseNotAllowed`；否则生成 `TrialOrder`（id, user_id, plan_code, amount=9.90, status=pending, created_at）。
2. `activate_trial_order(order_id)`：支付回调后开通 → 写 `UserSubscription`（plan_code=trial-9.9-monthly, start_at, end_at=+30d, auto_renew=False, status=active）+ `TrialPurchaseRecord`(status=completed)。发 `trial_activate` 埋点。
3. `expire_due_subscriptions(now)`：cron 扫描 end_at<=now 且 status=active 的尝鲜订阅 → 降级 status=expired + 发 `trial_churn` 埋点。
4. TDD 4 用例：下单成功、限购拦截（注入 guard 拒绝）、支付回调开通、到期降级。guard/仓储可注入 stub。
**DoD:** 下单链路通；到期降级可手动触发并验证状态迁移；order.py 暴露 HTTP/CLI 入口（若无框架则纯函数 + 注释说明接入点）。

## Task 4: 权益与配额执行层
**Files:** Update `src/entitlement/resolver.py`（不存在则创建）, Update `src/quota/limiter.py`（不存在则创建）, Create `tests/entitlement/test_trial_entitlement.py`
**Steps:**
1. 权益解析器：`resolve_entitlements(plan_code)` 支持 `trial-9.9-monthly` → 返回 SSOT entitlements 结构；未知名 plan_code 抛 `UnknownPlan`。同时支持 `free`/`basic-99` 占位（免费版/正价基础版值见 SSOT 对照）。
2. 配额限流器 `QuotaLimiter`：方法 `check_token(user, plan_code, tokens)` 超 200 万/月返 429；`check_concurrency(user, current)` 第 4 个并发返拒；`check_flagship_rate(user)` 超 20 次/h 限速。
3. TDD：尝鲜用户超 token 上限 → 429；第 4 并发被拒；旗舰超速被限；免费/正价用户行为不变（回归断言）。
**DoD:** 尝鲜用户按配置限流生效；正价/免费零回归。

## Task 5: 到期提醒与转化钩子
**Files:** Create `src/billing/jobs/trial_reminder.py`, Create `src/billing/services/conversion_coupon.py`, Create `tests/billing/test_trial_reminder.py`
**Steps:**
1. `run_trial_reminders(now)`：扫描 end_at - now ∈ {7,3,1} 天的 active 尝鲜订阅，按触点发提醒（站内信/邮件/推送，用可注入 Notifier 接口）。
2. 第 1 次（7 天）提醒附正价满减券（满 99 减 30）；第 3 次（1 天）附年付 8 折入口。`issue_conversion_coupon(user, type, value)` 写 `Coupon` 记录。
3. 发 `trial_renew_prompt` 埋点。
4. TDD 3 用例：到期前 7 天触发提醒 + 券发放、1 天触发年付入口、触达渠道选择（站内信必发、邮件按偏好）。
**DoD:** cron 可触发；券记录可查；`trial_renew_prompt` 上报。

## Task 6: 用户侧展示与购买入口
**Files:** Update `console/src/pages/pricing/`（尝鲜卡 + 倒计时）, Update `console/src/pages/home/`（新用户引导弹窗）, Create `console/tests/trial-card.test.tsx`
**Steps:**
1. 定价页新增"尝鲜版"卡片组件 `TrialCard`：划线原价 ¥99、尝鲜 ¥9.9、限购 1 次标签、倒计时（限时）。
2. 购买按钮按 `hasPurchasedTrial` 置灰显示"已享尝鲜价"，可点则跳转下单。
3. 新用户首登弹窗 `NewUserTrialModal` 引导至尝鲜价。
4. TDD（用现有测试框架；无则用 vitest/jest + @testing-library）：卡片渲染快照、限购置灰、弹窗触发 3 用例。
**DoD:** 卡片可见；限购置灰；下单跳转入口存在。若 console 仓库无 React 配置，则创建可独立导入的纯组件 + 注释说明接入，并写最小渲染测试（可用 tsx 直接断言组件导出与 props 行为）。

## Task 7: 埋点与转化数据看板
**Files:** Create `src/analytics/events/trial_funnel.yaml`, Update `website/src/pages/dashboard/trial-conversion/`（不存在则创建）, Create `tests/analytics/test_trial_funnel.py`
**Steps:**
1. `trial_funnel.yaml`：定义 6 事件 schema（view/purchase/activate/renew_prompt/convert_to_paid/churn），每事件含必填字段（user_id, plan_code, ts, value?）。
2. `trial_funnel.py`：聚合计算函数 `compute_funnel(events)` → 各阶段数、转化率（purchase→convert_to_paid）、ARPU、流失率、各触点贡献。
3. 看板页面占位组件展示北极星指标（转化率 ≥15% 目标线）。
4. TDD 2 用例：事件 schema 校验（必填字段缺失抛错）、漏斗聚合计算正确（给定事件序列得正确转化率）。
**DoD:** schema 可校验；聚合可算；看板组件存在并展示目标线。

---

## 子代理通用返回要求
- 返回：创建/修改的文件绝对或相对路径列表 + 对应 Task 的 `pytest`（或等效）输出摘要。
- 标注降级：若测试因环境（无 ORM/React 框架/依赖缺失，且非本 Task 范围）失败，按"静态审查"列明已覆盖逻辑点，不重试无关构建。
- 不执行 git commit/push；不跑全量构建。
