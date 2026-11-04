import { CalendarClock, Clock, MapPin, PoundSterling } from "lucide-react";
import type { Cost, Opportunity, PlanStep } from "../lib/types";
import { distanceLabel, durationLabel, gbp } from "../lib/format";
import { Badge } from "./ui";

export function FitRing({ score, size = 64 }: { score: number; size?: number }) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`Fit score ${score} out of 100`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--chart-1)" strokeWidth={6} strokeLinecap="round" strokeDasharray={`${(score / 100) * c} ${c}`} />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <span className="font-display text-lg font-extrabold leading-none">{score}</span>
      </div>
    </div>
  );
}

export function TypeBadge({ label }: { label: string }) {
  return <Badge tone="brand">{label}</Badge>;
}

export function OppFacts({ o }: { o: Pick<Opportunity, "firm" | "distance_miles" | "hours_per_week" | "weeks" | "hourly_rate" | "type" | "cost"> }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-ink-2">
      <span className="inline-flex items-center gap-1.5"><MapPin className="size-4 text-ink-3" />{distanceLabel(o.distance_miles, o.firm.town)}</span>
      <span className="inline-flex items-center gap-1.5"><Clock className="size-4 text-ink-3" />{o.hours_per_week} h/week</span>
      <span className="inline-flex items-center gap-1.5"><CalendarClock className="size-4 text-ink-3" />{durationLabel(o.weeks)}</span>
      <span className="inline-flex items-center gap-1.5 font-semibold text-good">
        <PoundSterling className="size-4" />
        {o.type === "first_job" && o.cost.annual_salary ? `${gbp(o.cost.annual_salary)} / year` : `${gbp(o.hourly_rate, 2)} / hour`}
      </span>
    </div>
  );
}

export function PlanTimeline({ plan }: { plan: PlanStep[] }) {
  return (
    <ol className="relative space-y-3 border-l-2 border-line pl-5">
      {plan.map((s, i) => (
        <li key={i} className="relative">
          <span className="absolute -left-[27px] top-1 size-3 rounded-full border-2 border-surface bg-brand" />
          <div className="text-xs font-semibold uppercase tracking-wide text-ink-3">{/^\d+$/.test(s.weeks) ? `Week ${s.weeks}` : /^\d/.test(s.weeks) ? `Weeks ${s.weeks}` : s.weeks}</div>
          <div className="text-sm font-semibold">{s.focus}</div>
          <div className="text-sm text-ink-2">{s.outcome}</div>
        </li>
      ))}
    </ol>
  );
}

export function CostTable({ cost }: { cost: Cost }) {
  const rows: [string, string][] =
    cost.kind === "salary"
      ? [["Hourly rate", gbp(cost.hourly_rate, 2)], ["Annual salary", gbp(cost.annual_salary ?? 0)], ["Monthly", gbp(cost.monthly_salary ?? 0)], ["FirstHire (3-month minimum)", gbp(cost.platform_fee)]]
      : [
          ["Wages", `${gbp(cost.wages ?? 0, 2)}`],
          ["Holiday pay accrual (12.07%)", gbp(cost.holiday_accrual ?? 0, 2)],
          ["FirstHire subscription", gbp(cost.platform_fee)],
        ];
  return (
    <div className="rounded-xl border border-line">
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k} className="border-b border-line last:border-0">
              <td className="px-4 py-2 text-ink-2">{k}</td>
              <td className="px-4 py-2 text-right font-medium tabular-nums">{v}</td>
            </tr>
          ))}
          {cost.kind === "fixed_term" && (
            <tr className="bg-surface-2">
              <td className="px-4 py-2.5 font-semibold">Estimated total</td>
              <td className="px-4 py-2.5 text-right font-display text-base font-extrabold tabular-nums">{gbp(cost.total_estimate ?? 0, 2)}</td>
            </tr>
          )}
        </tbody>
      </table>
      <p className="border-t border-line px-4 py-2 text-xs text-ink-3">Calculated by code, not AI. {cost.notes}</p>
    </div>
  );
}
