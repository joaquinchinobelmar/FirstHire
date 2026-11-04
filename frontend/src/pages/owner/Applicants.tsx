import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CalendarPlus, EyeOff, Handshake, Lock, Mail, MapPin, Phone, School, Star, ThumbsDown, Users } from "lucide-react";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, Modal, PageHeader, Select, Spinner, Textarea, Toast, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { STATUS_LABEL, dateLabel } from "../../lib/format";
import type { Applicant } from "../../lib/types";

type Resp = { applicants: Applicant[]; blind_review: boolean; note: string };
type Action = "shortlist" | "interview" | "offer" | "reject";

const FILTERS = ["all", "submitted", "shortlisted", "interview", "offered", "rejected"] as const;
const toneFor = (s: string) => (s === "offered" ? "good" : s === "interview" ? "brand" : s === "shortlisted" ? "ai" : s === "rejected" ? "bad" : "neutral") as "good" | "brand" | "ai" | "bad" | "neutral";

function ApplicantCard({ a, onAction }: { a: Applicant; onAction: (a: Applicant, action: Action) => void }) {
  const ev = a.evidence;
  const closed = ["offered", "rejected"].includes(a.status);
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="grid size-10 place-items-center rounded-full bg-surface-2 font-display text-sm font-bold text-ink-2">{a.identity ? a.identity.name.split(" ").map((n) => n[0]).join("") : <EyeOff className="size-4" />}</span>
            <div>
              <div className="font-bold">{a.identity ? a.identity.name : a.code}</div>
              <div className="text-xs text-ink-3">Applied {dateLabel(a.created_at)} · {a.opportunity.title}</div>
            </div>
          </div>
        </div>
        <Badge tone={toneFor(a.status)}>{STATUS_LABEL[a.status] ?? a.status}</Badge>
      </div>

      <div className="mt-4 rounded-xl border-l-4 border-brand bg-brand-soft/60 p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-brand">{a.opportunity.role_question}</div>
        <p className="mt-1.5 text-sm leading-relaxed">{a.answer}</p>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="space-y-3 text-sm">
          <div><span className="text-ink-3">Studied </span><span className="font-semibold">{ev.degree_subject || "—"}</span>{ev.graduation_year && <span className="text-ink-3"> · {ev.graduation_year}</span>}</div>
          <div className="flex flex-wrap gap-1.5">
            {ev.skills.map((s) => (
              <span key={s} className={cx("rounded-md px-2 py-0.5 text-xs font-medium", ev.skills_matching_role.includes(s) ? "bg-good-soft text-good" : "bg-surface-2 text-ink-2")}>
                {ev.skills_matching_role.includes(s) && "✓ "}{s}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-ink-2">
            <span className="inline-flex items-center gap-1"><MapPin className="size-4" />{ev.distance_miles == null ? "Local" : ev.distance_miles < 1 ? "Same town" : `${ev.distance_miles} mi away`}</span>
            <span>{ev.hours_available} h/week · {ev.availability || "flexible"}</span>
            {ev.term_time_limit && <span>Term-time limit {ev.term_time_limit} h</span>}
          </div>
        </div>
        <ul className="space-y-2 text-sm">
          {ev.experiences.map((e, i) => (
            <li key={i} className="rounded-lg bg-surface-2 p-2.5"><span className="font-semibold">{e.title}</span> <span className="text-ink-3">· {e.period}</span><div className="text-ink-2">{e.summary}</div></li>
          ))}
        </ul>
      </div>

      {a.identity ? (
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 rounded-xl bg-good-soft p-3 text-sm text-good">
          <a href={`mailto:${a.identity.email}`} className="inline-flex items-center gap-1.5 font-semibold hover:underline"><Mail className="size-4" />{a.identity.email}</a>
          {a.identity.phone && <span className="inline-flex items-center gap-1.5"><Phone className="size-4" />{a.identity.phone}</span>}
          <span className="inline-flex items-center gap-1.5"><School className="size-4" />{a.identity.university}</span>
          {a.interview_at && <span className="inline-flex items-center gap-1.5"><CalendarPlus className="size-4" />{a.interview_at}</span>}
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-surface-2 p-3 text-xs text-ink-2"><Lock className="size-4" /> Name, university and contact details unlock when you invite this person to interview.</div>
      )}

      {!closed && (
        <div className="mt-4 flex flex-wrap gap-2">
          {a.status === "submitted" && <Button size="sm" variant="secondary" icon={<Star className="size-4" />} onClick={() => onAction(a, "shortlist")}>Shortlist</Button>}
          {a.status !== "interview" && <Button size="sm" icon={<CalendarPlus className="size-4" />} onClick={() => onAction(a, "interview")}>Invite to interview</Button>}
          {a.status === "interview" && <Button size="sm" icon={<Handshake className="size-4" />} onClick={() => onAction(a, "offer")}>Make an offer</Button>}
          <Button size="sm" variant="ghost" icon={<ThumbsDown className="size-4" />} onClick={() => onAction(a, "reject")}>Not this time</Button>
        </div>
      )}
      {a.owner_note && closed && <p className="mt-3 text-xs text-ink-3">Your message: “{a.owner_note}”</p>}
    </Card>
  );
}

export default function Applicants() {
  const [params, setParams] = useSearchParams();
  const oppFilter = params.get("opportunity") ?? "all";
  const [data, setData] = useState<Resp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<(typeof FILTERS)[number]>("all");
  const [pending, setPending] = useState<{ a: Applicant; action: Action } | null>(null);
  const [note, setNote] = useState("");
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(() => api.get<Resp>("/owner/applicants").then(setData).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  const opportunities = useMemo(() => {
    const map = new Map<number, string>();
    data?.applicants.forEach((a) => map.set(a.opportunity.id, a.opportunity.title));
    return [...map.entries()];
  }, [data]);

  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner label="Loading applicants…" />;

  const list = data.applicants.filter((a) => (oppFilter === "all" || String(a.opportunity.id) === oppFilter) && (status === "all" || a.status === status));

  const act = (a: Applicant, action: Action) => {
    if (action === "shortlist") return decide(a, action, "", "");
    setNote("");
    setWhen("");
    setPending({ a, action });
  };

  async function decide(a: Applicant, action: Action, message: string, interviewAt: string) {
    setBusy(true);
    try {
      await api.post(`/owner/applications/${a.id}/decision`, { action, note: message, interview_at: interviewAt || null });
      setPending(null);
      setToast(action === "interview" ? "Invitation sent — contact details unlocked." : action === "reject" ? "Applicant notified kindly." : action === "offer" ? "Offer sent! A mentor will be assigned." : "Shortlisted.");
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Applicants" subtitle="Review evidence first. You make every decision — FirstHire's AI never ranks people." />
      <Alert tone="good" icon={<EyeOff className="size-4" />} className="mb-5">{data.note}</Alert>

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select
          className="sm:w-80"
          value={oppFilter}
          onChange={(e) => setParams(e.target.value === "all" ? {} : { opportunity: e.target.value })}
          options={[{ value: "all", label: "All opportunities" }, ...opportunities.map(([id, t]) => ({ value: String(id), label: t }))]}
        />
        <div className="flex flex-wrap gap-1.5">
          {FILTERS.map((f) => {
            const n = data.applicants.filter((a) => (oppFilter === "all" || String(a.opportunity.id) === oppFilter) && (f === "all" || a.status === f)).length;
            return (
              <button key={f} onClick={() => setStatus(f)} className={cx("cursor-pointer rounded-full px-3 py-1 text-sm font-semibold", status === f ? "bg-navy text-white" : "bg-surface text-ink-2 ring-1 ring-line hover:bg-surface-2")}>
                {f === "all" ? "All" : STATUS_LABEL[f]} <span className="opacity-60">{n}</span>
              </button>
            );
          })}
        </div>
      </div>

      {list.length === 0 ? (
        <EmptyState icon={<Users className="size-6" />} title="No applicants here yet">Publish an internal opportunity from the Growth Advisor — matching local graduates see it straight away.</EmptyState>
      ) : (
        <div className="grid gap-5 xl:grid-cols-2">{list.map((a) => <ApplicantCard key={a.id} a={a} onAction={act} />)}</div>
      )}

      <Modal
        open={!!pending}
        onClose={() => setPending(null)}
        title={pending?.action === "interview" ? "Invite to interview" : pending?.action === "offer" ? "Make an offer" : "Let them know kindly"}
      >
        {pending && (
          <div className="space-y-4">
            {pending.action === "interview" && (
              <>
                <Alert tone="brand">Inviting {pending.a.code} reveals their name and contact details to you. They'll see this in their access log.</Alert>
                <Field label="Proposed time"><Input value={when} onChange={(e) => setWhen(e.target.value)} placeholder="e.g. Tuesday 14:00 at our Gateshead site" /></Field>
              </>
            )}
            <Field label={pending.action === "reject" ? "Message (optional — we'll send a kind default)" : "Message to the applicant"}>
              <Textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder={pending.action === "reject" ? "Thanks for applying — your answer about… was great. We chose someone with more…" : "Looking forward to meeting you!"} />
            </Field>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPending(null)}>Cancel</Button>
              <Button variant={pending.action === "reject" ? "danger" : "primary"} loading={busy} onClick={() => decide(pending.a, pending.action, note, when)}>
                {pending.action === "interview" ? "Send invitation" : pending.action === "offer" ? "Send offer" : "Send"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}
