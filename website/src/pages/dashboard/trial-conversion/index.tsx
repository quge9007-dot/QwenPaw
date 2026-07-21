/**
 * dtcoder 9.9 尝鲜价套餐 — 转化漏斗看板页面。
 *
 * 北极星指标：purchase -> convert_to_paid 转化率，目标线 15%。
 * 计算逻辑见 ./computeFunnel.ts（与 Python 侧 src/analytics/trial_funnel.py 一致）。
 *
 * 该组件为占位 + 数据计算展示：接收一组埋点事件，渲染漏斗各阶段数、
 * 转化率（含 15% 目标线）、ARPU、流失率与各触点贡献。
 */
import { useMemo } from "react";
import {
  CONVERSION_RATE_TARGET,
  EVENT_TYPES,
  computeFunnel,
  type TrialFunnelEvent,
} from "./computeFunnel";

const STAGE_LABELS: Record<string, string> = {
  view: "浏览套餐",
  purchase: "购买尝鲜",
  activate: "激活使用",
  renew_prompt: "续费提醒",
  convert_to_paid: "转正价付费",
  churn: "流失",
};

const STAGE_COLORS: Record<string, string> = {
  view: "bg-slate-400",
  purchase: "bg-indigo-500",
  activate: "bg-sky-500",
  renew_prompt: "bg-amber-500",
  convert_to_paid: "bg-emerald-500",
  churn: "bg-rose-500",
};

function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}

function yuan(n: number): string {
  return `¥${n.toFixed(2)}`;
}

interface Props {
  /** 埋点事件序列；通常来自后端 / analytics pipeline。 */
  events: TrialFunnelEvent[];
  /** 可选自定义目标线，缺省 15%。 */
  target?: number;
}

export function TrialConversionDashboard({ events, target = CONVERSION_RATE_TARGET }: Props) {
  const report = useMemo(() => {
    try {
      return computeFunnel(events);
    } catch (err) {
      // 看板层兜底：事件非法时展示错误态而非整页崩溃。
      return { error: err instanceof Error ? err.message : String(err) } as {
        error: string;
      };
    }
  }, [events]);

  if ("error" in report) {
    return (
      <section className="rounded-xl border border-rose-300 bg-rose-50 p-6 text-rose-700">
        <h2 className="text-lg font-semibold">转化看板数据错误</h2>
        <p className="mt-2 text-sm">{report.error}</p>
      </section>
    );
  }

  const maxCount = Math.max(1, ...EVENT_TYPES.map((s) => report.stageCounts[s]));
  const meetsTarget = report.northStar.meetsTarget;

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">dtcoder 9.9 尝鲜价套餐 · 转化漏斗看板</h1>
        <p className="mt-1 text-sm text-slate-500">
          北极星指标：购买 → 正价付费转化率，目标线 {pct(target)}
        </p>
      </header>

      {/* 北极星指标卡 */}
      <div className="rounded-xl border p-6 shadow-sm">
        <div className="flex items-baseline justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              转化率（purchase → convert_to_paid）
            </p>
            <p className="mt-1 text-4xl font-bold">{pct(report.conversionRate)}</p>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              meetsTarget
                ? "bg-emerald-100 text-emerald-700"
                : "bg-rose-100 text-rose-700"
            }`}
          >
            {meetsTarget ? "达标" : "未达标"} · 目标 {pct(target)}
          </span>
        </div>
        {/* 目标线进度条 */}
        <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className={`h-full ${meetsTarget ? "bg-emerald-500" : "bg-amber-500"}`}
            style={{ width: `${Math.min(100, (report.conversionRate / target) * 100)}%` }}
          />
        </div>
      </div>

      {/* 次级指标 */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Metric label="购买用户数" value={String(report.purchasers)} />
        <Metric label="转化用户数" value={String(report.converts)} />
        <Metric label="ARPU" value={yuan(report.arpu)} />
        <Metric label="流失率" value={pct(report.churnRate)} />
      </div>

      {/* 漏斗各阶段 */}
      <div className="rounded-xl border p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">漏斗阶段分布</h2>
        <ul className="space-y-3">
          {EVENT_TYPES.map((stage) => {
            const count = report.stageCounts[stage];
            const width = `${(count / maxCount) * 100}%`;
            return (
              <li key={stage} className="flex items-center gap-3">
                <span className="w-28 shrink-0 text-sm text-slate-600">
                  {STAGE_LABELS[stage]}
                </span>
                <div className="relative h-6 flex-1 rounded bg-slate-100">
                  <div
                    className={`h-full rounded ${STAGE_COLORS[stage]}`}
                    style={{ width }}
                  />
                </div>
                <span className="w-10 shrink-0 text-right text-sm tabular-nums">{count}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {/* 各触点贡献 */}
      <div className="rounded-xl border p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">各触点对转化的贡献</h2>
        <ul className="space-y-3">
          {Object.entries(report.touchpointContribution).map(([tp, share]) => (
            <li key={tp} className="flex items-center gap-3">
              <span className="w-28 shrink-0 text-sm text-slate-600">
                {STAGE_LABELS[tp] ?? tp}
              </span>
              <div className="relative h-6 flex-1 rounded bg-slate-100">
                <div
                  className="h-full rounded bg-sky-500"
                  style={{ width: `${share * 100}%` }}
                />
              </div>
              <span className="w-12 shrink-0 text-right text-sm tabular-nums">
                {pct(share)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

export default TrialConversionDashboard;
