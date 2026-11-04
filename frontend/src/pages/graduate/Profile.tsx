import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, EyeOff, FileUp, Plus, Save, ShieldCheck, Sparkles, Trash2, Wand2 } from "lucide-react";
import { AiBadge, Alert, Button, Card, Field, Input, Modal, PageHeader, Select, Spinner, TagInput, Textarea, Toast, cx } from "../../components/ui";
import { api } from "../../lib/api";
import type { CvDraft, Experience, Passport } from "../../lib/types";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <Card className="p-6">
      <h2 className="text-lg font-bold">{title}</h2>
      {description && <p className="mt-0.5 text-sm text-ink-2">{description}</p>}
      <div className="mt-5">{children}</div>
    </Card>
  );
}

export default function Profile() {
  const [p, setP] = useState<Passport | null>(null);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<CvDraft | null>(null);
  const [drafting, setDrafting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { api.get<Passport>("/student/passport").then(setP).catch((e) => setError(e.message)); }, []);

  const set = <K extends keyof Passport>(key: K, value: Passport[K]) => {
    setP((prev) => (prev ? { ...prev, [key]: value } : prev));
    setDirty(true);
  };

  const completeness = useMemo(() => {
    if (!p) return 0;
    const checks = [p.headline, p.degree, p.grad_year, p.home_town, p.skills.length >= 3, p.experiences.length >= 1, p.interests.length >= 1, p.availability, p.cv_text];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [p]);

  if (error && !p) return <Alert tone="bad">{error}</Alert>;
  if (!p) return <Spinner label="Loading your Passport…" />;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const { ai_preview: _a, towns: _t, email: _e, updated_at: _u, ...body } = p;
      const fresh = await api.put<Passport>("/student/passport", body);
      setP(fresh);
      setDirty(false);
      setToast("Passport saved. Your matches will refresh.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const upload = async (file: File) => {
    setDrafting(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.post<{ cv_text: string; draft: CvDraft }>("/student/passport/cv", form);
      setP((prev) => (prev ? { ...prev, cv_text: res.cv_text } : prev));
      setDraft(res.draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setDrafting(false);
    }
  };

  const draftFromText = async () => {
    setDrafting(true);
    setError(null);
    try {
      setDraft(await api.post<CvDraft>("/student/passport/autofill", { cv_text: p.cv_text }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't draft from CV");
    } finally {
      setDrafting(false);
    }
  };

  const applyDraft = () => {
    if (!draft) return;
    setP((prev) => prev && ({
      ...prev,
      headline: draft.headline || prev.headline,
      skills: Array.from(new Set([...prev.skills, ...draft.skills])),
      experiences: draft.experiences.length ? [...prev.experiences, ...draft.experiences.filter((d) => !prev.experiences.some((e) => e.title === d.title))] : prev.experiences,
      interests: Array.from(new Set([...prev.interests, ...draft.interests])),
    }));
    setDirty(true);
    setDraft(null);
    setToast("Draft added — review it, then save.");
  };

  const updateExp = (i: number, patch: Partial<Experience>) => set("experiences", p.experiences.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));

  return (
    <div>
      <PageHeader
        title="My Passport"
        subtitle="Fill this in once. It powers your matches — and firms see your skills before your name."
        actions={
          <>
            <Link to="/graduate/opportunities" className="inline-flex h-10 items-center gap-2 rounded-lg border border-line bg-surface px-4 text-sm font-semibold hover:bg-surface-2">See my matches <ArrowRight className="size-4" /></Link>
            <Button onClick={save} loading={saving} disabled={!dirty} icon={<Save className="size-4" />}>{dirty ? "Save changes" : "Saved"}</Button>
          </>
        }
      />
      {error && <Alert tone="bad" className="mb-5">{error}</Alert>}

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <Section title="Start from your CV" description="Upload a PDF or paste the text. AI drafts your skills and experience — you review everything before it's saved.">
            <div className="flex flex-col gap-3 sm:flex-row">
              <input ref={fileRef} type="file" accept=".pdf,.txt,.md" className="hidden" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
              <Button variant="secondary" icon={<FileUp className="size-4" />} onClick={() => fileRef.current?.click()} loading={drafting}>Upload CV (PDF)</Button>
              <Button variant="ai" icon={<Wand2 className="size-4" />} onClick={draftFromText} disabled={p.cv_text.trim().length < 30} loading={drafting}>Draft Passport from CV text</Button>
            </div>
            <Field label="CV text" hint="Contact details (email, phone, postcode, links) are stripped automatically before AI sees it. The original file is not stored." className="mt-4">
              <Textarea rows={5} value={p.cv_text} onChange={(e) => set("cv_text", e.target.value)} placeholder="Paste your CV here…" />
            </Field>
          </Section>

          <Section title="About you">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Full name" hint="Hidden from firms until interview."><Input value={p.full_name} onChange={(e) => set("full_name", e.target.value)} /></Field>
              <Field label="Phone" hint="Hidden from firms until interview."><Input value={p.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
              <Field label="Headline" className="sm:col-span-2"><Input value={p.headline} onChange={(e) => set("headline", e.target.value)} placeholder="e.g. Computer Science graduate who loves building useful things" /></Field>
              <Field label="Degree"><Input value={p.degree} onChange={(e) => set("degree", e.target.value)} placeholder="BSc Computer Science" /></Field>
              <Field label="University" hint="Hidden from firms and from the AI."><Input value={p.university} onChange={(e) => set("university", e.target.value)} /></Field>
              <Field label="Graduation year"><Input type="number" value={p.grad_year ?? ""} onChange={(e) => set("grad_year", e.target.value ? Number(e.target.value) : null)} /></Field>
            </div>
          </Section>

          <Section title="Where and when you can work" description="We only show opportunities you can realistically reach — no London relocations.">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Home town"><Select value={p.home_town} onChange={(e) => set("home_town", e.target.value)} options={p.towns.map((t) => ({ value: t, label: t }))} /></Field>
              <Field label={`Travel radius: ${p.max_travel_miles} miles`}>
                <input type="range" min={3} max={40} value={p.max_travel_miles} onChange={(e) => set("max_travel_miles", Number(e.target.value))} className="mt-3 w-full accent-[var(--brand)]" />
              </Field>
              <Field label="Hours available per week"><Input type="number" min={4} max={48} value={p.hours_per_week} onChange={(e) => set("hours_per_week", Number(e.target.value))} /></Field>
              <Field label="Availability"><Input value={p.availability} onChange={(e) => set("availability", e.target.value)} placeholder="e.g. Weekdays; café shifts at weekends" /></Field>
            </div>
            <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-xl bg-surface-2 p-3 text-sm">
              <input type="checkbox" checked={p.on_student_visa} onChange={(e) => set("on_student_visa", e.target.checked)} className="mt-0.5 size-4 accent-[var(--brand)]" />
              <span><span className="font-semibold">I'm on a Student visa</span><br /><span className="text-ink-2">We'll hide part-time roles over 20 h/week in term time and ask you to confirm your own limit before applying.</span></span>
            </label>
          </Section>

          <Section title="Skills & interests">
            <Field label="Skills" hint="Press Enter after each one. Include soft skills from part-time work — they count.">
              <TagInput value={p.skills} onChange={(v) => set("skills", v)} placeholder="Python, Customer service, Canva…" />
            </Field>
            <Field label="Sectors you're interested in" className="mt-4">
              <TagInput value={p.interests} onChange={(v) => set("interests", v)} placeholder="Technology, Food & hospitality…" />
            </Field>
          </Section>

          <Section title="Experience" description="Jobs, projects, volunteering, societies. A café job is real evidence of reliability and handling pressure.">
            <div className="space-y-4">
              {p.experiences.map((e, i) => (
                <div key={i} className="rounded-xl border border-line p-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <Input value={e.title} onChange={(ev) => updateExp(i, { title: ev.target.value })} placeholder="Role / project" />
                    <Input value={e.organisation} onChange={(ev) => updateExp(i, { organisation: ev.target.value })} placeholder="Organisation" />
                    <Input value={e.period} onChange={(ev) => updateExp(i, { period: ev.target.value })} placeholder="2024–2026" />
                  </div>
                  <div className="mt-3 flex gap-3">
                    <Textarea rows={2} value={e.summary} onChange={(ev) => updateExp(i, { summary: ev.target.value })} placeholder="What did you do and achieve?" />
                    <button aria-label="Remove experience" onClick={() => set("experiences", p.experiences.filter((_, idx) => idx !== i))} className="cursor-pointer self-start rounded-lg p-2 text-ink-3 hover:bg-bad-soft hover:text-bad"><Trash2 className="size-4" /></button>
                  </div>
                </div>
              ))}
              <Button variant="secondary" icon={<Plus className="size-4" />} onClick={() => set("experiences", [...p.experiences, { title: "", organisation: "", period: "", summary: "" }])}>Add experience</Button>
            </div>
          </Section>
        </div>

        {/* Sidebar */}
        <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <Card className="p-6">
            <div className="flex items-end justify-between">
              <div>
                <div className="text-sm font-medium text-ink-2">Passport strength</div>
                <div className="font-display text-4xl font-extrabold">{completeness}%</div>
              </div>
              <span className={cx("text-sm font-semibold", completeness >= 80 ? "text-good" : "text-warn")}>{completeness >= 80 ? "Ready to match" : "Add more detail"}</span>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${completeness}%` }} />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-2"><ShieldCheck className="size-5 text-good" /><h3 className="font-bold">Privacy controls</h3></div>
            <label className="mt-4 flex cursor-pointer items-start gap-3 text-sm">
              <input type="checkbox" checked={p.consent_ai} onChange={(e) => set("consent_ai", e.target.checked)} className="mt-0.5 size-4 accent-[var(--brand)]" />
              <span><span className="font-semibold">Use AI to match me</span><br /><span className="text-ink-2">Off = a simple offline matcher; nothing is sent to the AI.</span></span>
            </label>
            <div className="mt-5 rounded-xl bg-surface-2 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold"><EyeOff className="size-4" /> What the AI sees</div>
              <dl className="space-y-1.5 text-xs">
                {Object.entries(p.ai_preview).filter(([k]) => !k.startsWith("_")).map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[110px_1fr] gap-2">
                    <dt className="text-ink-3">{k.replaceAll("_", " ")}</dt>
                    <dd className="break-words text-ink">{Array.isArray(v) ? (v.length ? v.map((x) => (typeof x === "object" ? (x as Experience).title : String(x))).join(", ") : "—") : v == null || v === "" ? "—" : String(v)}</dd>
                  </div>
                ))}
              </dl>
              <div className="mt-3 border-t border-line pt-3 text-xs text-ink-2">
                <span className="font-semibold text-good">Never sent:</span> {(p.ai_preview._removed_before_ai as string[]).join(", ")}.
              </div>
              {dirty && <div className="mt-2 text-xs text-warn">Save to update this preview.</div>}
            </div>
            <Link to="/trust" className="mt-4 inline-block text-sm font-semibold text-brand hover:underline">Access log, export & delete →</Link>
          </Card>
        </aside>
      </div>

      <Modal open={!!draft} onClose={() => setDraft(null)} title="Passport draft from your CV" wide>
        {draft && (
          <div className="space-y-4">
            <div className="flex items-center justify-between"><p className="text-sm text-ink-2">{draft.summary}</p><AiBadge source={draft.source} /></div>
            <div><div className="text-sm font-semibold">Headline</div><p className="text-sm">{draft.headline}</p></div>
            <div>
              <div className="text-sm font-semibold">Skills found ({draft.skills.length})</div>
              <div className="mt-1.5 flex flex-wrap gap-1.5">{draft.skills.map((s) => <span key={s} className="rounded-md bg-brand-soft px-2 py-0.5 text-xs font-medium text-brand">{s}</span>)}</div>
            </div>
            {draft.experiences.length > 0 && (
              <div>
                <div className="text-sm font-semibold">Experience</div>
                <ul className="mt-1.5 space-y-2">{draft.experiences.map((e, i) => <li key={i} className="rounded-lg bg-surface-2 p-3 text-sm"><span className="font-semibold">{e.title}</span> · {e.organisation} <span className="text-ink-3">({e.period})</span><div className="text-ink-2">{e.summary}</div></li>)}</ul>
              </div>
            )}
            <Alert tone="ai" icon={<Sparkles className="size-4" />}>Nothing is saved until you click “Save changes”. Edit anything that isn't right.</Alert>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setDraft(null)}>Discard</Button>
              <Button onClick={applyDraft}>Add to my Passport</Button>
            </div>
          </div>
        )}
      </Modal>
      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}
