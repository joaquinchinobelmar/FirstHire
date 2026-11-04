import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BadgeCheck, Building2, CheckCheck, Lightbulb, RefreshCw, Send, Sparkles, TrendingDown, TrendingUp, Users, Wand2, X,
} from "lucide-react";
import { ImpactChart } from "../../components/ImpactChart";
import { OpportunityEditor } from "../../components/OpportunityEditor";
import { TypeBadge } from "../../components/OpportunityBits";
import { AiBadge, Alert, Badge, Button, Card, Modal, PageHeader, Spinner, Textarea, Toast, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { gbp, monthLabel, pct } from "../../lib/format";
import type { AdvisorResult, Dashboard, Insight } from "../../lib/types";

const EXAMPLES = [
  "Our phone rings non-stop at lunch and we lose orders. Customers keep asking if they can order online.",
  "I spend every evening doing admin and rotas instead of growing the business.",
  "We have great reviews but our Instagram is quiet and weekday afternoons are dead.",
];

const CATEGORY_TONE: Record<string, "brand" | "ai" | "good" | "warn" | "neutral"> = {
  digital: "brand", marketing: "ai", data: "brand", operations: "warn", people: "good", finance: "neutral",
};

function Kpi({ label, value, delta, hint }: { label: string; value: string; delta?: number; hint?: string }) {
  return (
    <Card className="p-5">
      <div className="text-sm font-medium text-ink-2">{label}</div>
      <div className="mt-1 font-display text-3xl font-extrabold tabular-nums">{value}</div>
      {delta !== undefined ? (
        <div className={cx("mt-1 inline-flex items-center gap-1 text-xs font-semibold", delta >= 0 ? "text-good" : "text-bad")}>
          {delta >= 0 ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />} {pct(delta)} {hint}
        </div>
      ) : hint ? <div className="mt-1 text-xs text-ink-3">{hint}</div> : null}
    </Card>
  );
}

function InsightCard({ i, onDraft, onStatus, drafting }: { i: Insight; onDraft: () => void; onStatus: (s: Insight["status"]) => void; drafting: boolean }) {
  return (
    <Card className={cx("flex flex-col p-5", i.status === "dismissed" && "opacity-60")}>
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone={CATEGORY_TONE[i.category] ?? "neutral"} className="capitalize">{i.category}</Badge>
        <Badge tone="neutral">Effort: {i.effort}</Badge>
        {i.status === "accepted" && <Badge tone="good">Role published</Badge>}
        {i.status === "implemented" && <Badge tone="good" icon={<CheckCheck className="size-3" />}>Implemented {i.implemented_at ? monthLabel(i.implemented_at) : ""}</Badge>}
      </div>
      <h3 className="mt-2.5 font-bold leading-snug">{i.title}</h3>
      <p className="mt-1 text-sm text-ink-2">{i.problem}</p>
      <div className="mt-3 rounded-lg bg-surface-2 p-3 text-sm">
        <div><span className="font-semibold">Suggestion: </span>{i.recommendation}</div>
        <div className="mt-1 text-ink-2"><span className="font-semibold text-ink">Impact: </span>{i.expected_impact}</div>
      </div>
      <div className="mt-2 text-xs text-ink-3">Evidence: {i.evidence}</div>
      {i.status === "new" && (
        <div className="mt-auto flex flex-wrap gap-2 pt-4">
          {i.opportunity_type !== "none" && (
            <Button size="sm" variant="ai" icon={<Wand2 className="size-4" />} loading={drafting} onClick={onDraft}>Find a student for this</Button>
          )}
          <Button size="sm" variant="secondary" icon={<CheckCheck className="size-4" />} onClick={() => onStatus("implemented")}>Done it</Button>
          <Button size="sm" variant="ghost" icon={<X className="size-4" />} onClick={() => onStatus("dismissed")}>Dismiss</Button>
        </div>
      )}
    </Card>
  );
}

export default function Advisor() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [asking, setAsking] = useState(false);
  const [result, setResult] = useState<AdvisorResult | null>(null);
  const [modalResult, setModalResult] = useState<AdvisorResult | null>(null);
  const [draftingId, setDraftingId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showDismissed, setShowDismissed] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(() => api.get<Dashboard>("/owner/dashboard").then(setD).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  if (error && !d) return <Alert tone="bad">{error}</Alert>;
  if (!d) return <Spinner label="Loading your business dashboard…" />;

  const ask = async () => {
    setAsking(true);
    setError(null);
    try {
      setResult(await api.post<AdvisorResult>("/owner/advisor", { prompt }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "The advisor couldn't answer");
    } finally {
      setAsking(false);
    }
  };

  const draftInsight = async (i: Insight) => {
    setDraftingId(i.id);
    try {
      setModalResult(await api.post<AdvisorResult>(`/owner/insights/${i.id}/draft`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't draft");
    } finally {
      setDraftingId(null);
    }
  };

  const setStatus = async (i: Insight, status: Insight["status"]) => {
    await api.patch(`/owner/insights/${i.id}`, { status });
    load();
  };

  const refreshInsights = async () => {
    setRefreshing(true);
    try {
      const r = await api.post<{ source: string; count: number }>("/owner/insights/refresh");
      setToast(`${r.count} fresh insights from ${r.source === "claude" ? "Claude" : "the offline engine"}.`);
      await load();
    } finally {
      setRefreshing(false);
    }
  };

  const published = () => {
    setResult(null);
    setModalResult(null);
    setPrompt("");
    setToast("Published! Matching graduates will see it in their feed.");
    load();
  };

  const k = d.kpis;
  const ch = d.companies_house;
  const visibleInsights = d.insights.filter((i) => showDismissed || i.status !== "dismissed");
  const openInsights = visibleInsights.filter((i) => i.status === "new");
  const doneInsights = visibleInsights.filter((i) => i.status !== "new");

  return (
    <div>
      <PageHeader
        title={d.firm.name}
        subtitle={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="inline-flex items-center gap-1"><Building2 className="size-4" />{d.firm.sector} · {d.firm.town} · {d.firm.employees} staff</span>
            {ch && (
              <span className="inline-flex items-center gap-1 text-good" title={`Source: ${ch.source}`}>
                <BadgeCheck className="size-4" /> Companies House {ch.company_number} · {ch.company_status}
                {ch.source === "synthetic-snapshot" && <span className="text-ink-3">(synthetic demo record)</span>}
              </span>
            )}
          </span>
        }
        actions={<Badge tone={d.ai_mode === "claude" ? "ai" : "neutral"} icon={<Sparkles className="size-3" />}>{d.ai_mode === "claude" ? "Claude AI connected" : "Offline demo mode"}</Badge>}
      />

      {k && (
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Kpi label={`Revenue · ${monthLabel(k.month)}`} value={gbp(k.revenue)} delta={k.revenue_vs_prev3_pct} hint="vs prior 3 months" />
          <Kpi label="Customers this month" value={new Intl.NumberFormat("en-GB").format(k.customers)} />
          <Kpi label="AI suggestions implemented" value={String(k.implemented_count)} hint="tracked against your numbers" />
          <Kpi label="Open roles · new applicants" value={`${k.open_roles} · ${k.new_applicants}`} hint="internal to FirstHire" />
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.25fr_1fr]">
        {/* Advisor prompt */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2"><span className="rounded-lg bg-ai-soft p-2 text-ai"><Lightbulb className="size-5" /></span><h2 className="text-lg font-bold">Ask the Growth Advisor</h2></div>
          </div>
          <p className="mt-2 text-sm text-ink-2">Describe what's slowing the business down. The advisor suggests fixes and, if it helps, scopes a fair paid role for a local graduate. Nothing is published until you approve it.</p>
          <Textarea rows={4} className="mt-4" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="e.g. We're always busy but I don't know which dishes actually make money…" />
          <div className="mt-2 flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex) => (
              <button key={ex} onClick={() => setPrompt(ex)} className="cursor-pointer rounded-full border border-line px-3 py-1 text-xs text-ink-2 hover:border-ai hover:text-ai">{ex.slice(0, 48)}…</button>
            ))}
          </div>
          <div className="mt-4 flex justify-end">
            <Button variant="ai" icon={<Send className="size-4" />} loading={asking} disabled={prompt.trim().length < 10} onClick={ask}>Get suggestions</Button>
          </div>
          {asking && <p className="mt-3 text-sm text-ink-3">Thinking through your business data… this can take a few seconds.</p>}
          {error && <Alert tone="bad" className="mt-3">{error}</Alert>}
        </Card>

        {/* Impact chart */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Since you acted on AI suggestions</h2>
          </div>
          <div className="mt-3"><ImpactChart data={d.metrics} events={d.impact} /></div>
          {d.impact.map((im) => (
            <div key={im.insight_id} className="mt-3 rounded-xl border border-line p-3 text-sm">
              <div className="font-semibold">{im.title} <span className="font-normal text-ink-3">· {monthLabel(im.month)}</span></div>
              <div className="mt-1 grid grid-cols-2 gap-2">
                <div>Revenue <b className={im.revenue_change_pct >= 0 ? "text-good" : "text-bad"}>{pct(im.revenue_change_pct)}</b> <span className="text-ink-3">({gbp(im.revenue_before)} → {gbp(im.revenue_after)}/mo)</span></div>
                <div>Customers <b className={im.customers_change_pct >= 0 ? "text-good" : "text-bad"}>{pct(im.customers_change_pct)}</b></div>
              </div>
              <div className="mt-1 text-xs text-ink-3">Average of 3 months after vs 3 months before. A correlation, not proof — seasonality also plays a part.</div>
            </div>
          ))}
        </Card>
      </div>

      {result && (
        <Card className="animate-rise mt-6 border-ai/40 p-6">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-bold">Advisor suggestions</h2>
            <AiBadge source={result.source} />
          </div>
          <p className="mt-2 text-ink-2">{result.understanding}</p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {result.suggestions.map((s) => (
              <div key={s.title} className="rounded-xl bg-surface-2 p-4 text-sm">
                <div className="flex items-start justify-between gap-2"><div className="font-semibold">{s.title}</div><Badge tone="neutral">{s.effort}</Badge></div>
                <p className="mt-1 text-ink-2">{s.recommendation}</p>
                <p className="mt-1 text-xs text-ink-3">{s.why}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 border-t border-line pt-6">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-bold">Draft internal opportunity</h3>
              <TypeBadge label={result.opportunity.type_label} />
              {!result.needs_hire && <Badge tone="warn">Optional — you may not need a hire</Badge>}
            </div>
            <OpportunityEditor draft={result.opportunity} source={result.source} onPublished={published} />
          </div>
        </Card>
      )}

      {/* Insights */}
      <section className="mt-10">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-extrabold">What your business might be missing</h2>
            <p className="text-sm text-ink-2">The advisor reviews your firm profile, reviews and numbers to spot opportunities.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => setShowDismissed((v) => !v)}>{showDismissed ? "Hide dismissed" : "Show dismissed"}</Button>
            <Button variant="secondary" size="sm" icon={<RefreshCw className={cx("size-4", refreshing && "animate-spin")} />} loading={refreshing} onClick={refreshInsights}>Re-analyse my business</Button>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {openInsights.map((i) => <InsightCard key={i.id} i={i} drafting={draftingId === i.id} onDraft={() => draftInsight(i)} onStatus={(s) => setStatus(i, s)} />)}
        </div>
        {doneInsights.length > 0 && (
          <>
            <h3 className="mt-8 mb-3 text-sm font-semibold uppercase tracking-wide text-ink-3">Acted on</h3>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {doneInsights.map((i) => <InsightCard key={i.id} i={i} drafting={false} onDraft={() => undefined} onStatus={() => undefined} />)}
            </div>
          </>
        )}
      </section>

      {/* Opportunities */}
      <section className="mt-10">
        <h2 className="mb-4 text-xl font-extrabold">Your internal opportunities</h2>
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="border-b border-line text-left text-ink-3">
              <tr><th className="px-5 py-3 font-medium">Role</th><th className="px-3 py-3 font-medium">Type</th><th className="px-3 py-3 font-medium">Pay</th><th className="px-3 py-3 font-medium">Applicants</th><th className="px-3 py-3 font-medium">Status</th><th className="px-5 py-3" /></tr>
            </thead>
            <tbody>
              {d.opportunities.map((o) => (
                <tr key={o.id} className="border-b border-line last:border-0">
                  <td className="px-5 py-3">
                    <div className="font-semibold">{o.title}</div>
                    {(o.source === "claude" || o.source === "offline") && <div className="text-xs text-ai">Scoped with the Growth Advisor</div>}
                  </td>
                  <td className="px-3 py-3">{o.type_label}</td>
                  <td className="px-3 py-3 tabular-nums">{gbp(o.hourly_rate, 2)}/h · {o.hours_per_week}h</td>
                  <td className="px-3 py-3"><span className="inline-flex items-center gap-1"><Users className="size-4 text-ink-3" />{o.applicant_total ?? 0}{(o.applicant_counts?.submitted ?? 0) > 0 && <Badge tone="brand">{o.applicant_counts?.submitted} new</Badge>}</span></td>
                  <td className="px-3 py-3"><Badge tone={o.status === "published" ? "good" : "neutral"}>{o.status === "published" ? "Open" : "Closed"}</Badge></td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Link to={`/business/applicants?opportunity=${o.id}`} className="inline-flex h-8 items-center rounded-lg border border-line px-3 text-sm font-semibold hover:bg-surface-2">Review</Link>
                      <Button size="sm" variant="ghost" onClick={async () => { await api.patch(`/owner/opportunities/${o.id}`, { status: o.status === "published" ? "closed" : "published" }); load(); }}>
                        {o.status === "published" ? "Close" : "Reopen"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      <Modal open={!!modalResult} onClose={() => setModalResult(null)} title="Turn this insight into an opportunity" wide>
        {modalResult && (
          <div>
            <div className="mb-4 flex items-start justify-between gap-3"><p className="text-sm text-ink-2">{modalResult.understanding}</p><AiBadge source={modalResult.source} /></div>
            <OpportunityEditor draft={modalResult.opportunity} source={modalResult.source} insightId={modalResult.insight_id} onPublished={published} />
          </div>
        )}
      </Modal>
      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}
