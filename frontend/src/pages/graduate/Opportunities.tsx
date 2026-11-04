import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ChevronDown, Compass, Heart, LayoutGrid, MapPin, RefreshCw, Rocket, Send, Sparkles, TrendingUp, X,
} from "lucide-react";
import { CostTable, FitRing, OppFacts, PlanTimeline, TypeBadge } from "../../components/OpportunityBits";
import { AiBadge, Alert, Badge, Button, Card, EmptyState, Modal, PageHeader, Spinner, Textarea, Toast, cx } from "../../components/ui";
import { api } from "../../lib/api";
import type { MatchedOpportunity, MatchesResponse } from "../../lib/types";

function MatchCard({ o, onApply, onPass, featured }: { o: MatchedOpportunity; onApply: () => void; onPass: () => void; featured?: boolean }) {
  const [open, setOpen] = useState(!!featured);
  const fromAdvisor = o.source === "claude" || o.source === "offline";
  return (
    <Card className={cx("flex flex-col p-5", featured && "p-6 sm:p-7")}>
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <TypeBadge label={o.type_label} />
            {fromAdvisor && <Badge tone="ai" icon={<Sparkles className="size-3" />}>New · scoped with AI</Badge>}
            <Badge tone="neutral">Internal · members only</Badge>
          </div>
          <h3 className={cx("mt-2 font-bold leading-snug", featured ? "text-2xl" : "text-lg")}>{o.title}</h3>
          <div className="text-sm text-ink-2">{o.firm.name} · {o.firm.sector} · {o.firm.employees} staff</div>
        </div>
        <FitRing score={o.match.fit_score} size={featured ? 76 : 60} />
      </div>
      <div className="mt-3"><OppFacts o={o} /></div>

      <div className="mt-4 rounded-xl bg-ai-soft p-4">
        <div className="flex items-center gap-1.5 text-sm font-semibold text-ai"><Sparkles className="size-4" /> Why it fits you</div>
        <p className="mt-1 text-sm font-medium text-ink">{o.match.headline}</p>
        <ul className="mt-2 space-y-1 text-sm text-ink-2">
          {o.match.reasons.map((r) => <li key={r} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-ai" />{r}</li>)}
        </ul>
      </div>

      <button onClick={() => setOpen((v) => !v)} className="mt-3 inline-flex cursor-pointer items-center gap-1 self-start text-sm font-semibold text-brand">
        {open ? "Hide details" : "Role details, plan & career path"} <ChevronDown className={cx("size-4 transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="mt-4 grid gap-5 border-t border-line pt-4 md:grid-cols-2">
          <div className="space-y-4">
            <p className="text-sm text-ink-2">{o.summary}</p>
            <div>
              <div className="mb-1.5 text-sm font-semibold">What you'll do</div>
              <ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">{o.tasks.map((t) => <li key={t}>{t}</li>)}</ul>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {o.skills_required.map((s) => <span key={s} className="rounded-md bg-surface-2 px-2 py-0.5 text-xs font-medium">{s}</span>)}
              {o.skills_nice.map((s) => <span key={s} className="rounded-md border border-dashed border-line px-2 py-0.5 text-xs text-ink-2">{s} (bonus)</span>)}
            </div>
            {o.removed_requirements.length > 0 && (
              <p className="text-xs text-good">✓ Not required: {o.removed_requirements.join(", ")}</p>
            )}
          </div>
          <div className="space-y-4">
            <PlanTimeline plan={o.plan} />
            {o.match.skill_gaps.length > 0 && (
              <div className="text-sm"><span className="font-semibold">You'll learn: </span><span className="text-ink-2">{o.match.skill_gaps.join(", ")}</span></div>
            )}
            <div className="rounded-xl border border-line p-3 text-sm">
              <div className="flex items-center gap-1.5 font-semibold"><TrendingUp className="size-4 text-brand" /> Local career path</div>
              <p className="mt-0.5 text-ink-2">{o.match.career_path}</p>
              <p className="mt-2 text-ink-2"><span className="font-semibold text-ink">Your edge: </span>{o.match.transferable_experience}</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-5 flex gap-2 pt-1">
        <Button variant="secondary" icon={<X className="size-4" />} onClick={onPass} className="flex-1 sm:flex-none">Not for me</Button>
        <Button icon={<Send className="size-4" />} onClick={onApply} className="flex-1">Apply</Button>
      </div>
    </Card>
  );
}

export default function Opportunities() {
  const [data, setData] = useState<MatchesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"discover" | "grid">("discover");
  const [index, setIndex] = useState(0);
  const [anim, setAnim] = useState<"" | "swipe-left" | "swipe-right">("");
  const [applying, setApplying] = useState<MatchedOpportunity | null>(null);
  const [answer, setAnswer] = useState("");
  const [confirmHours, setConfirmHours] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.get<MatchesResponse>(`/student/matches${refresh ? "?refresh=true" : ""}`));
      setIndex(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load matches");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const removeLocal = (id: number) => setData((d) => (d ? { ...d, matches: d.matches.filter((m) => m.id !== id) } : d));

  const pass = async (o: MatchedOpportunity) => {
    setAnim("swipe-left");
    await api.post(`/student/opportunities/${o.id}/pass`).catch(() => undefined);
    setTimeout(() => { removeLocal(o.id); setAnim(""); }, 260);
  };

  const submit = async () => {
    if (!applying) return;
    setSubmitting(true);
    setApplyError(null);
    try {
      await api.post(`/student/opportunities/${applying.id}/apply`, { answer, confirm_hours: confirmHours });
      const id = applying.id;
      setApplying(null);
      setAnswer("");
      setConfirmHours(false);
      setAnim("swipe-right");
      setTimeout(() => {
        removeLocal(id);
        setAnim("");
        setData((d) => (d ? { ...d, applications_this_month: d.applications_this_month + 1 } : d));
      }, 260);
      setToast("Application sent! Track it in Applications.");
    } catch (e) {
      setApplyError(e instanceof Error ? e.message : "Couldn't apply");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !data) return <Spinner label="Finding local opportunities that fit you…" />;
  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return null;

  const current = data.matches[Math.min(index, data.matches.length - 1)];
  const f = data.filtered;
  const hidden = f.outside_radius + f.outside_region + f.over_hour_limit;

  return (
    <div>
      <PageHeader
        title="Opportunities for you"
        subtitle={<>Paid, local roles matched to your Passport. <span className="whitespace-nowrap">Applications this month: <b>{data.applications_this_month}/{data.monthly_limit}</b></span></>}
        actions={
          <>
            <div className="flex rounded-lg border border-line bg-surface p-0.5">
              {([["discover", "Discover", Compass], ["grid", "All matches", LayoutGrid]] as const).map(([v, label, Icon]) => (
                <button key={v} onClick={() => setView(v)} className={cx("flex cursor-pointer items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-semibold", view === v ? "bg-brand-soft text-brand" : "text-ink-2")}>
                  <Icon className="size-4" /> {label}
                </button>
              ))}
            </div>
            <Button variant="secondary" icon={<RefreshCw className={cx("size-4", loading && "animate-spin")} />} onClick={() => load(true)} disabled={loading}>Re-match</Button>
          </>
        }
      />

      <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_auto]">
        <Card className="p-5">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold text-ink-2">Your profile, as local employers will see it</div>
            <AiBadge source={data.source} />
          </div>
          <p className="mt-1.5">{data.profile_summary}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">{data.strengths.map((s) => <Badge key={s} tone="brand">{s}</Badge>)}</div>
          {data.note && <p className="mt-2 text-xs text-ink-3">{data.note}</p>}
        </Card>
        <Card className="flex items-center gap-4 p-5 lg:w-80">
          <span className="rounded-xl bg-good-soft p-3 text-good"><MapPin className="size-5" /></span>
          <div className="text-sm">
            <div className="font-semibold">Local first: within {f.radius_miles} mi of {f.home_town}</div>
            <div className="text-ink-2">{hidden > 0 ? `${hidden} role${hidden > 1 ? "s" : ""} hidden as too far or over your hours.` : "Nothing hidden."} <Link to="/graduate/profile" className="font-semibold text-brand hover:underline">Change</Link></div>
          </div>
        </Card>
      </div>

      {data.matches.length === 0 ? (
        <EmptyState icon={<Rocket className="size-6" />} title="You've seen every local match for now">
          New internal opportunities appear as local firms publish them. Try widening your travel radius or{" "}
          <button className="cursor-pointer font-semibold text-brand" onClick={async () => { await api.del("/student/passes"); load(); }}>bring back passed roles</button>.
        </EmptyState>
      ) : view === "discover" ? (
        <div className="mx-auto max-w-3xl">
          <div className="mb-3 flex items-center justify-between text-sm text-ink-3">
            <span>Match {Math.min(index, data.matches.length - 1) + 1} of {data.matches.length} · best fit first</span>
            <span className="hidden sm:inline">Not for me ← · → Apply</span>
          </div>
          <div key={current.id} className={cx("animate-rise", anim)}>
            <MatchCard o={current} featured onPass={() => pass(current)} onApply={() => setApplying(current)} />
          </div>
          {data.matches.length > 1 && (
            <div className="mt-4 flex justify-center gap-2">
              <Button variant="ghost" size="sm" disabled={index === 0} onClick={() => setIndex((i) => Math.max(0, i - 1))}>Previous</Button>
              <Button variant="ghost" size="sm" icon={<Heart className="size-4" />} disabled={index >= data.matches.length - 1} onClick={() => setIndex((i) => i + 1)}>Skip for now</Button>
            </div>
          )}
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          {data.matches.map((o) => <MatchCard key={o.id} o={o} onPass={() => pass(o)} onApply={() => setApplying(o)} />)}
        </div>
      )}

      <Modal open={!!applying} onClose={() => setApplying(null)} title={applying ? `Apply: ${applying.title}` : ""} wide>
        {applying && (
          <div className="space-y-5">
            <div className="text-sm text-ink-2">{applying.firm.name} · <OppFactsInline o={applying} /></div>
            <div className="rounded-xl border-l-4 border-brand bg-brand-soft p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-brand">The firm's question</div>
              <p className="mt-1 font-semibold">{applying.role_question}</p>
            </div>
            <div>
              <Textarea rows={6} value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Answer with a real example. Firms read this first." />
              <div className={cx("mt-1 text-right text-xs", answer.trim().length >= 40 ? "text-good" : "text-ink-3")}>{answer.trim().length} / 40+ characters</div>
            </div>
            <label className="flex cursor-pointer items-start gap-3 text-sm">
              <input type="checkbox" checked={confirmHours} onChange={(e) => setConfirmHours(e.target.checked)} className="mt-0.5 size-4 accent-[var(--brand)]" />
              <span>I can commit to <b>{applying.hours_per_week} h/week</b>{applying.weeks ? ` for ${applying.weeks} weeks` : ""}, and it fits my visa limit if I have one.</span>
            </label>
            <details className="rounded-xl border border-line p-3 text-sm">
              <summary className="cursor-pointer font-semibold">What the firm will see</summary>
              <p className="mt-2 text-ink-2">Your answer, degree subject, skills, experience and availability. <b>Not</b> your name, university, email or phone — those are shared only if they invite you to interview, and it'll show in your access log.</p>
            </details>
            <details className="text-sm">
              <summary className="cursor-pointer font-semibold">Pay breakdown</summary>
              <div className="mt-2"><CostTable cost={applying.cost} /></div>
            </details>
            {applyError && <Alert tone="bad">{applyError}</Alert>}
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setApplying(null)}>Cancel</Button>
              <Button onClick={submit} loading={submitting} disabled={answer.trim().length < 40 || !confirmHours} icon={<Send className="size-4" />}>Send application</Button>
            </div>
          </div>
        )}
      </Modal>
      <Toast message={toast} onDone={() => setToast(null)} />
      <KeyboardNav enabled={view === "discover" && !applying && !!current} onLeft={() => current && pass(current)} onRight={() => current && setApplying(current)} />
    </div>
  );
}

function OppFactsInline({ o }: { o: MatchedOpportunity }) {
  return <span>{o.hours_per_week} h/week · {o.weeks ? `${o.weeks} weeks` : "permanent"}</span>;
}

function KeyboardNav({ enabled, onLeft, onRight }: { enabled: boolean; onLeft: () => void; onRight: () => void }) {
  useEffect(() => {
    if (!enabled) return;
    const h = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.closest("input, textarea, select")) return;
      if (e.key === "ArrowLeft") onLeft();
      if (e.key === "ArrowRight") onRight();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [enabled, onLeft, onRight]);
  return null;
}
