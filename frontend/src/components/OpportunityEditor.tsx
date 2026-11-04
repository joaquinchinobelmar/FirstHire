import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Megaphone, Sparkles } from "lucide-react";
import { api } from "../lib/api";
import type { Cost, DraftOpportunity, OppType } from "../lib/types";
import { CostTable, PlanTimeline } from "./OpportunityBits";
import { Alert, Button, Field, Input, Select, TagInput, Textarea } from "./ui";

const TYPES: { value: OppType; label: string }[] = [
  { value: "paid_project", label: "Paid project" },
  { value: "part_time", label: "Part-time role" },
  { value: "internship", label: "Internship" },
  { value: "first_job", label: "First job" },
];

export function OpportunityEditor({
  draft, source, insightId, onPublished,
}: { draft: DraftOpportunity; source: "claude" | "offline"; insightId?: number; onPublished: (id: number) => void }) {
  const [d, setD] = useState<DraftOpportunity>(draft);
  const [cost, setCost] = useState<Cost>(draft.cost);
  const [problems, setProblems] = useState<string[]>([]);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setD(draft); setCost(draft.cost); }, [draft]);

  // Live, code-calculated cost & rule check
  useEffect(() => {
    const t = setTimeout(() => {
      api.post<{ cost: Cost; problems: string[] }>("/owner/wage-estimate", {
        type: d.type, hourly_rate: Number(d.hourly_rate) || 0, hours_per_week: Number(d.hours_per_week) || 1,
        weeks: d.type === "first_job" ? null : Number(d.weeks) || 0,
      }).then((r) => { setCost(r.cost); setProblems(r.problems); }).catch(() => undefined);
    }, 250);
    return () => clearTimeout(t);
  }, [d.type, d.hourly_rate, d.hours_per_week, d.weeks]);

  const set = <K extends keyof DraftOpportunity>(k: K, v: DraftOpportunity[K]) => setD((p) => ({ ...p, [k]: v }));

  const publish = async () => {
    setPublishing(true);
    setError(null);
    try {
      const res = await api.post<{ opportunity_id: number }>("/owner/opportunities", {
        ...d, tasks: d.tasks.map((t) => t.trim()).filter(Boolean), weeks: d.type === "first_job" ? null : d.weeks,
        insight_id: insightId ?? null, source,
      });
      onPublished(res.opportunity_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't publish");
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-[1fr_200px]">
          <Field label="Role title"><Input value={d.title} onChange={(e) => set("title", e.target.value)} /></Field>
          <Field label="Opportunity type"><Select value={d.type} onChange={(e) => set("type", e.target.value as OppType)} options={TYPES} /></Field>
        </div>
        <Field label="Summary"><Textarea rows={3} value={d.summary} onChange={(e) => set("summary", e.target.value)} /></Field>
        <Field label="Tasks" hint="One per line">
          <Textarea rows={4} value={d.tasks.join("\n")} onChange={(e) => set("tasks", e.target.value.split("\n"))} onBlur={() => set("tasks", d.tasks.map((t) => t.trim()).filter(Boolean))} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Skills needed"><TagInput value={d.skills_required} onChange={(v) => set("skills_required", v)} /></Field>
          <Field label="Nice to have"><TagInput value={d.skills_nice} onChange={(v) => set("skills_nice", v)} /></Field>
        </div>
        {d.removed_requirements.length > 0 && (
          <Alert tone="good" icon={<CheckCircle2 className="size-4" />}>
            <b>Removed to widen the talent pool:</b> {d.removed_requirements.join(", ")}
          </Alert>
        )}
        <Field label="Role-specific question for applicants" hint="Applicants must answer this — it replaces the cover letter.">
          <Textarea rows={2} value={d.role_question} onChange={(e) => set("role_question", e.target.value)} />
        </Field>
        <div>
          <div className="mb-2 text-sm font-medium">Plan with fortnightly mentor check-ins</div>
          <PlanTimeline plan={d.plan} />
        </div>
        {d.reasoning && (
          <div className="rounded-xl bg-ai-soft p-4 text-sm">
            <div className="mb-1 flex items-center gap-1.5 font-semibold text-ai"><Sparkles className="size-4" /> Why the AI scoped it this way</div>
            <p className="text-ink-2">{d.reasoning}</p>
          </div>
        )}
      </div>

      <aside className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <Field label="£ / hour"><Input type="number" step="0.01" min={0} value={d.hourly_rate} onChange={(e) => set("hourly_rate", Number(e.target.value))} /></Field>
          <Field label="h / week"><Input type="number" min={1} value={d.hours_per_week} onChange={(e) => set("hours_per_week", Number(e.target.value))} /></Field>
          <Field label="Weeks"><Input type="number" min={0} disabled={d.type === "first_job"} value={d.type === "first_job" ? "" : d.weeks ?? ""} onChange={(e) => set("weeks", Number(e.target.value))} /></Field>
        </div>
        <CostTable cost={cost} />
        {problems.length > 0 ? (
          <Alert tone="warn" icon={<AlertTriangle className="size-4" />}>{problems.map((p) => <div key={p}>{p}</div>)}</Alert>
        ) : (
          <Alert tone="good" icon={<CheckCircle2 className="size-4" />}>Pay and hours pass FirstHire's fair-work rules.</Alert>
        )}
        {error && <Alert tone="bad">{error}</Alert>}
        <Button size="lg" className="w-full" icon={<Megaphone className="size-4" />} loading={publishing} disabled={problems.length > 0} onClick={publish}>
          Publish internal opportunity
        </Button>
        <p className="text-xs text-ink-3">Internal = visible only to verified FirstHire graduates, not posted publicly. You can close it anytime.</p>
      </aside>
    </div>
  );
}
