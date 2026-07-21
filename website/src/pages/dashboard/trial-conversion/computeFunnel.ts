/**
 * dtcoder 9.9 尝鲜价套餐 — 转化漏斗看板：数据计算层。
 *
 * 与 `src/analytics/trial_funnel.py` 保持语义一致；调整逻辑时两侧同步。
 *
 * 北极星指标：purchase -> convert_to_paid 转化率，目标线 15%。
 */

export const PLAN_CODE = "dtcoder_trial_9_9" as const;
export const CONVERSION_RATE_TARGET = 0.15;

/** 漏斗阶段（生命周期顺序） */
export const EVENT_TYPES = [
  "view",
  "purchase",
  "activate",
  "renew_prompt",
  "convert_to_paid",
  "churn",
] as const;

export type EventType = (typeof EVENT_TYPES)[number];

/** 单条埋点事件 */
export interface TrialFunnelEvent {
  event: EventType;
  user_id: string;
  plan_code: string;
  ts: string; // ISO-8601
  value?: number;
}

/** 看板聚合结果 */
export interface FunnelReport {
  stageCounts: Record<EventType, number>;
  uniqueUsers: number;
  purchasers: number;
  converts: number;
  churns: number;
  conversionRate: number;
  churnRate: number;
  arpu: number;
  totalRevenue: number;
  touchpointContribution: Record<string, number>;
  northStar: {
    metric: "conversion_rate";
    target: number;
    value: number;
    meetsTarget: boolean;
  };
}

const VALID_EVENTS = new Set<string>(EVENT_TYPES);

/**
 * 校验单条事件。违反约束时抛出 Error。
 * 镜像 Python 侧 validate_event 的规则。
 */
export function validateEvent(event: unknown): asserts event is TrialFunnelEvent {
  if (typeof event !== "object" || event === null) {
    throw new Error("event must be an object");
  }
  const ev = event as Record<string, unknown>;
  const type = ev.event;
  if (typeof type !== "string" || !VALID_EVENTS.has(type)) {
    throw new Error(`unknown event type: ${String(type)}`);
  }
  for (const field of ["user_id", "plan_code", "ts"] as const) {
    const val = ev[field];
    if (val === undefined || val === null || val === "") {
      throw new Error(`event ${type} missing required field ${field}`);
    }
  }
  if (ev.user_id !== undefined && typeof ev.user_id !== "string") {
    throw new Error("user_id must be string");
  }
  if (ev.plan_code !== undefined && ev.plan_code !== PLAN_CODE) {
    throw new Error(`plan_code must be ${PLAN_CODE}, got ${String(ev.plan_code)}`);
  }
  if (typeof ev.ts !== "string") {
    throw new Error("ts must be ISO-8601 string");
  }
  if (ev.value !== undefined && ev.value !== null) {
    if (typeof ev.value !== "number" || Number.isNaN(ev.value)) {
      throw new Error("value must be a number");
    }
    if ((ev.value as number) < 0) {
      throw new Error("value must be >= 0");
    }
  }
}

/**
 * 聚合事件序列，输出漏斗指标。
 *
 * conversion_rate = converts / purchasers
 * churn_rate       = churns / purchasers
 * arpu             = sum(convert_to_paid.value) / purchasers
 */
export function computeFunnel(events: readonly TrialFunnelEvent[]): FunnelReport {
  for (const ev of events) validateEvent(ev);

  const stageCounts = {
    view: 0,
    purchase: 0,
    activate: 0,
    renew_prompt: 0,
    convert_to_paid: 0,
    churn: 0,
  } as Record<EventType, number>;

  const users = new Set<string>();
  const purchasers = new Set<string>();
  const activated = new Set<string>();
  const renewPrompted = new Set<string>();
  const converted = new Set<string>();
  const churned = new Set<string>();
  let totalRevenue = 0;

  for (const ev of events) {
    stageCounts[ev.event] += 1;
    users.add(ev.user_id);
    switch (ev.event) {
      case "purchase":
        purchasers.add(ev.user_id);
        break;
      case "activate":
        activated.add(ev.user_id);
        break;
      case "renew_prompt":
        renewPrompted.add(ev.user_id);
        break;
      case "convert_to_paid":
        converted.add(ev.user_id);
        totalRevenue += ev.value ?? 0;
        break;
      case "churn":
        churned.add(ev.user_id);
        break;
      default:
        break;
    }
  }

  const purchaserN = purchasers.size;
  const convertN = converted.size;
  const churnN = churned.size;

  const conversionRate = purchaserN ? convertN / purchaserN : 0;
  const churnRate = purchaserN ? churnN / purchaserN : 0;
  const arpu = purchaserN ? totalRevenue / purchaserN : 0;

  const touchpointContribution: Record<string, number> = {};
  const sets: Record<string, Set<string>> = {
    view: users,
    purchase: purchasers,
    activate: activated,
    renew_prompt: renewPrompted,
  };
  for (const [tp, set] of Object.entries(sets)) {
    let intersect = 0;
    for (const u of converted) if (set.has(u)) intersect += 1;
    touchpointContribution[tp] = convertN ? intersect / convertN : 0;
  }

  return {
    stageCounts,
    uniqueUsers: users.size,
    purchasers: purchaserN,
    converts: convertN,
    churns: churnN,
    conversionRate,
    churnRate,
    arpu,
    totalRevenue,
    touchpointContribution,
    northStar: {
      metric: "conversion_rate",
      target: CONVERSION_RATE_TARGET,
      value: conversionRate,
      meetsTarget: conversionRate >= CONVERSION_RATE_TARGET,
    },
  };
}
