import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Impact } from "../lib/types";
import { gbp, monthLabel } from "../lib/format";
import { cx } from "./ui";

type Metric = "revenue" | "customers";
type Point = { month: string; revenue: number; customers: number };

const fmt = (metric: Metric, v: number) => (metric === "revenue" ? gbp(v) : new Intl.NumberFormat("en-GB").format(v));
const short = (metric: Metric, v: number) => (metric === "revenue" ? `£${Math.round(v / 1000)}k` : `${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}`);

function ChartTooltip({ active, payload, metric, events }: { active?: boolean; payload?: { payload: Point }[]; metric: Metric; events: Impact[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const ev = events.find((e) => e.month === p.month);
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-sm shadow-lg">
      <div className="text-xs text-ink-3">{monthLabel(p.month)}</div>
      <div className="font-semibold tabular-nums text-ink">{fmt(metric, p[metric])}</div>
      {ev && <div className="mt-1 max-w-56 text-xs text-ink-2">▲ Implemented: {ev.title}</div>}
    </div>
  );
}

/** Single-series trend with markers for each implemented AI suggestion. One axis, one measure at a time. */
export function ImpactChart({ data, events }: { data: Point[]; events: Impact[] }) {
  const [metric, setMetric] = useState<Metric>("revenue");
  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="text-sm text-ink-2">Monthly {metric === "revenue" ? "revenue" : "customers"}, last 12 months</div>
        <div className="flex rounded-lg border border-line p-0.5" role="tablist" aria-label="Metric">
          {(["revenue", "customers"] as const).map((m) => (
            <button key={m} role="tab" aria-selected={metric === m} onClick={() => setMetric(m)} className={cx("cursor-pointer rounded-md px-3 py-1 text-xs font-semibold capitalize", metric === m ? "bg-brand-soft text-brand" : "text-ink-3")}>
              {m}
            </button>
          ))}
        </div>
      </div>
      <div className="h-64 w-full" role="img" aria-label={`Line chart of monthly ${metric} with markers where AI suggestions were implemented`}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 24, right: 12, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="fill-1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.18} />
                <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeWidth={1} />
            <XAxis dataKey="month" tickFormatter={monthLabel} tick={{ fill: "var(--ink-3)", fontSize: 12 }} tickLine={false} axisLine={{ stroke: "var(--chart-grid)" }} interval="preserveStartEnd" minTickGap={16} />
            <YAxis tickFormatter={(v) => short(metric, v)} tick={{ fill: "var(--ink-3)", fontSize: 12 }} tickLine={false} axisLine={false} width={48} domain={["auto", "auto"]} />
            <Tooltip content={<ChartTooltip metric={metric} events={events} />} cursor={{ stroke: "var(--ink-3)", strokeWidth: 1 }} />
            {events.map((e) => (
              <ReferenceLine key={e.insight_id} x={e.month} stroke="var(--ai)" strokeWidth={1.5} label={{ value: "AI suggestion live", position: "top", fill: "var(--ai)", fontSize: 11, fontWeight: 600 }} />
            ))}
            <Area type="monotone" dataKey={metric} stroke="var(--chart-1)" strokeWidth={2} fill="url(#fill-1)" strokeLinejoin="round" strokeLinecap="round"
              dot={false} activeDot={{ r: 5, fill: "var(--chart-1)", stroke: "var(--surface)", strokeWidth: 2 }} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-2 text-xs text-ink-3">
        <summary className="cursor-pointer">View as table</summary>
        <table className="mt-2 w-full text-left">
          <thead><tr className="text-ink-2"><th className="py-1">Month</th><th>Revenue</th><th>Customers</th></tr></thead>
          <tbody>{data.map((d) => <tr key={d.month} className="border-t border-line"><td className="py-1">{monthLabel(d.month)}</td><td className="tabular-nums">{gbp(d.revenue)}</td><td className="tabular-nums">{d.customers}</td></tr>)}</tbody>
        </table>
      </details>
    </div>
  );
}
