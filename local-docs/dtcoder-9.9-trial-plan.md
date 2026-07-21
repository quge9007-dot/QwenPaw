# dtcoder 9.9 尝鲜价套餐 Implementation Plan

## 1. 背景与目标

dtcoder 计划面向**新用户**推出 **9.9 元尝鲜价** 套餐，作为付费版的低门槛引流入口。核心目标：

- 降低首次付费心理门槛，将免费用户转化为付费用户
- 通过限时/限购制造紧迫感，提升首月转化率
- 建立尝鲜 → 正价订阅/年付的转化漏斗，沉淀付费用户资产

### 1.1 设计原则（自主决策）

基于行业最佳实践（Cursor/Copilot 等同类工具的尝鲜/首月优惠惯例）与风险最低兜底：

1. **限购防薅**：每自然用户限购 1 次，按账号 + 设备 + 支付方式三重去重
2. **额度可控**：尝鲜版权益 = 正价基础版权益，但叠加**月度 token 上限**与**并发上限**，避免被白嫖高成本算力
3. **默认不自动续费**：到期默认降级为免费版，避免自动扣款投诉；续费需用户主动确认
4. **价格锚点明确**：展示原价（如 99 元/月）划线价，9.9 仅首月，次月恢复正价
5. **转化钩子前置**：到期前 7/3/1 天多触点提醒 + 正价券 + 年付折扣引导

### 1.2 非目标（本期不做）

- 不做阶梯式多人拼团/裂变（风控复杂度高，二期）
- 不做企业版/团队版尝鲜（B 端单独规划）
- 不做算力分级（GPU/高并发）尝鲜

---

## 2. 套餐方案设计（SSOT）

### 2.1 套餐定义

| 字段 | 值 |
|---|---|
| 套餐代号 | `trial-9.9-monthly` |
| 套餐名称 | dtcoder 尝鲜版（首月） |
| 价格 | ¥9.90 |
| 计费周期 | 月付（首次） |
| 有效期 | 30 天 |
| 原价锚点 | ¥99.00/月（正价基础版） |
| 购买限制 | 每自然用户限购 1 次 |
| 自动续费 | 默认关闭，到期降级免费版 |

### 2.2 权益矩阵（尝鲜版 vs 正价基础版 vs 免费版）

| 权益项 | 免费版 | 尝鲜版 9.9 | 正价基础版 99 |
|---|---|---|---|
| 月度 token 上限 | 50万 | 200万 | 无限(合理使用) |
| 并行会话数 | 1 | 3 | 5 |
| 上下文窗口 | 32K | 128K | 200K |
| 模型档位 | 基础模型 | 基础+旗舰(限速) | 全模型 |
| 旗舰模型速率限制 | - | 20 次/小时 | 不限 |
| 高级技能/插件 | ✗ | ✓ | ✓ |
| 优先客服队列 | ✗ | ✓ | ✓ |
| 历史记录保留 | 7 天 | 90 天 | 无限 |

> 自主决策：尝鲜版给到"够用但不够爽"的体验，权益高于免费版、略低于正价基础版，制造升级动机。

### 2.3 限购与风控规则

1. **限购维度**（满足任一即拦截重复购买）：
   - 用户账号 ID
   - 设备指纹（浏览器 + 客户端硬件特征哈希）
   - 支付方式（微信 openid / 支付宝 uid / 卡号末四位）
2. **风控阈值**：
   - 同一支付方式绑定不同账号 ≥ 2 → 触发人工复核
   - 同一 IP 段 24h 内成交 ≥ 5 单 → 限流 + 风控告警
   - 新注册账号 < 24h 直接购买尝鲜价 → 延迟 1h 到账 + 设备校验
3. **退款策略**：尝鲜价一经使用（产生 token 消耗）不支持退款；未使用 7 天内可退。

### 2.4 生命周期与转化路径

```
新用户注册 → 首页弹窗/引导页 → 购买尝鲜价 9.9
   → 到账开通(30天) → 到期前 7/3/1 天提醒
   → 用户选择：① 升级正价版(送满减券) ② 年付(8折) ③ 不续费降级免费版
```

转化埋点关键节点：`trial_view` / `trial_purchase` / `trial_activate` / `trial_renew_prompt` / `trial_convert_to_paid` / `trial_churn`。

### 2.5 定价与财务口径

- 尝鲜价收入按"促销折扣"入账，差额（99-9.9=89.1）计入营销费用，不影响正价 ARPU 口径
- 9.9 元为含税价，税率按平台所在口径拆分
- 转化率目标：尝鲜用户 30 天内转正价 ≥ 15%（北极星指标）

---

## 3. 实施任务分解

> 按 writing-plans 规范：每个 Task 独立可验证、有明确 Files / Steps(TDD) / Definition of Done。

### Task 1: 套餐与 SKU 配置数据模型

**Files:**
- Create: `src/billing/models/trial_plan.py`
- Create: `tests/billing/test_trial_plan_model.py`
- Update: `src/billing/migrations/xxxx_add_trial_plan.py`

**Steps:**
- [ ] 定义 `TrialPlan` 模型：plan_code、price、duration_days、entitlements(JSON)、quota_limits(JSON)、purchase_limit、is_active
- [ ] 定义 `TrialPurchaseRecord` 模型：user_id、device_fingerprint、payment_method_hash、purchased_at、status
- [ ] 编写迁移脚本，插入 `trial-9.9-monthly` 默认配置
- [ ] TDD：先写模型校验测试（限购=1、价格>0、有效期>0）再实现

**Definition of Done:** 模型单测通过；迁移可在空库与现有库正向执行；默认套餐可通过 `get_plan('trial-9.9-monthly')` 查询到。

### Task 2: 限购与风控校验服务

**Files:**
- Create: `src/billing/services/trial_guard.py`
- Create: `tests/billing/test_trial_guard.py`

**Steps:**
- [ ] 实现 `check_purchase_eligibility(user, device, payment)` 返回 `(allowed, reason)`
- [ ] 三重去重规则：账号 / 设备 / 支付方式
- [ ] 风控阈值触发：记录 `RiskEvent` 并返回人工复核标记
- [ ] TDD：覆盖首次可购、重复账号、重复设备、重复支付、新注册延迟、IP 限流 6 个用例

**Definition of Done:** 6 个用例全绿；风控告警写入事件表；服务可被下单接口注入调用。

### Task 3: 下单与计费周期服务

**Files:**
- Create: `src/billing/services/trial_order.py`
- Update: `src/billing/api/order.py`
- Create: `tests/billing/test_trial_order.py`

**Steps:**
- [ ] `create_trial_order(user, plan_code, payment_channel)`：校验 → 生成订单 → 支付回调后开通
- [ ] 开通动作：写入 `UserSubscription`，周期 30 天，`auto_renew=False`
- [ ] 到期处理：cron 扫描到期订阅，降级为免费版，触发 `trial_churn` 埋点
- [ ] TDD：覆盖下单成功、限购拦截、支付回调开通、到期降级 4 个用例

**Definition of Done:** 下单全链路可跑通；到期降级 cron 可手动触发并验证状态迁移。

### Task 4: 权益与配额执行层

**Files:**
- Update: `src/entitlement/resolver.py`
- Update: `src/quota/limiter.py`
- Create: `tests/entitlement/test_trial_entitlement.py`

**Steps:**
- [ ] 权益解析器支持 `trial-9.9-monthly` → 解析为 token 上限/并发/上下文窗口/模型档位
- [ ] 配额限流器按尝鲜版阈值执行（200万 token/月、3 并发、20 次/h 旗舰模型）
- [ ] TDD：尝鲜用户请求超 token 上限返回 429；并发第 4 个被拒；旗舰模型超速被限

**Definition of Done:** 尝鲜用户在网关层按配置限流生效；正价/免费用户行为不变（回归无影响）。

### Task 5: 到期提醒与转化钩子

**Files:**
- Create: `src/billing/jobs/trial_reminder.py`
- Create: `src/billing/services/conversion_coupon.py`
- Create: `tests/billing/test_trial_reminder.py`

**Steps:**
- [ ] 到期前 7/3/1 天分别发送提醒（站内信 + 邮件 + 推送）
- [ ] 第 1 次提醒附"正价满减券"（如满 99 减 30）
- [ ] 第 3 次提醒附"年付 8 折"入口
- [ ] TDD：到期前 7 天触发提醒、券发放、触达渠道选择 3 个用例

**Definition of Done:** 提醒 cron 可触发；券发放记录可查；转化埋点 `trial_renew_prompt` 上报。

### Task 6: 用户侧展示与购买入口

**Files:**
- Update: `console/src/pages/pricing/` (尝鲜价卡片 + 倒计时)
- Update: `console/src/pages/home/` (新用户引导弹窗)
- Create: `console/tests/trial-card.test.tsx`

**Steps:**
- [ ] 定价页新增"尝鲜版"卡片：划线原价 ¥99、尝鲜 ¥9.9、限购 1 次标签
- [ ] 购买按钮校验限购状态，已购则置灰显示"已享尝鲜价"
- [ ] 新用户首登弹窗引导至尝鲜价
- [ ] TDD：卡片渲染、限购置灰、弹窗触发 3 个用例

**Definition of Done:** 定价页可见尝鲜卡；限购用户正确置灰；端到端下单可跳转支付。

### Task 7: 埋点与转化数据看板

**Files:**
- Create: `src/analytics/events/trial_funnel.yaml`
- Update: `website/src/pages/dashboard/trial-conversion/`
- Create: `tests/analytics/test_trial_funnel.py`

**Steps:**
- [ ] 定义漏斗事件：view/purchase/activate/renew_prompt/convert_to_paid/churn
- [ ] 看板展示：尝鲜购买量、转化率、ARPU、流失率、各触点转化贡献
- [ ] TDD：事件 schema 校验、漏斗聚合计算 2 个用例

**Definition of Done:** 漏斗事件可上报；看板可展示北极星指标（转化率 ≥15% 目标线）。

---

## 4. 验收标准（整体 DoD）

- [ ] 新用户可完成 9.9 元下单 → 开通 → 使用全流程
- [ ] 重复账号/设备/支付方式被正确拦截限购
- [ ] 尝鲜用户 token/并发/旗舰模型限流生效
- [ ] 到期自动降级免费版，无自动扣款
- [ ] 到期前 7/3/1 天提醒与券发放到位
- [ ] 转化漏斗看板可查看北极星指标
- [ ] 正价/免费用户行为零回归

## 5. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 黄牛批量薅 9.9 | 三重去重 + 新注册延迟到账 + IP 限流 + 风控告警 |
| 尝鲜用户成本失控（token 超支） | 月度 200 万 token 上限 + 旗舰模型限速 |
| 自动续费投诉 | 默认关闭自动续费，到期降级 |
| 正价用户流失转尝鲜 | 限购 1 次 + 仅新用户/未付费用户可见入口 |

回滚方案：套餐配置 `is_active=false` 即可下架尝鲜价入口，不影响已开通用户的 30 天有效期。

## 6. 上线节奏

- Task 1–3 为后端核心链路，先行
- Task 4 依赖 Task 1 配置
- Task 5–7 可并行，依赖 Task 3 下单链路
- 灰度：先 5% 新用户可见，观察转化与风控 3 天后全量
