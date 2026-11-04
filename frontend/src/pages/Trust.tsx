import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, Eye, FileLock2, History, ServerCog, ShieldCheck, Trash2 } from "lucide-react";
import { Logo } from "../components/AppShell";
import { Alert, Button, Card, Modal } from "../components/ui";
import { api } from "../lib/api";
import { homeFor, useAuth } from "../lib/auth";
import { dateLabel } from "../lib/format";

type LogEntry = { actor: string; action: string; detail: string; created_at: string };

const SECTIONS = [
  {
    icon: <FileLock2 className="size-5" />,
    title: "What we collect, and why",
    items: [
      "Graduates: your Passport (degree, skills, experience, availability, travel radius) and your applications — only to match you with local opportunities.",
      "Businesses: firm details, the problems you describe, and anonymised business metrics — only to generate suggestions and scope roles.",
      "We do not collect photos, and we never ask for age, ethnicity, religion or other protected characteristics.",
    ],
  },
  {
    icon: <Eye className="size-5" />,
    title: "Who can see your data",
    items: [
      "Firms see an applicant's answer, skills and experience first. Name, university and contact details are revealed only when they invite you to interview.",
      "Every reveal or decision appears in your access log below.",
      "Internal opportunities are visible only to signed-in FirstHire members — they are not posted publicly.",
    ],
  },
  {
    icon: <ServerCog className="size-5" />,
    title: "How the AI uses it",
    items: [
      "Matching runs on an anonymised profile: name, email, phone, university and contact details inside your CV are removed before any AI call.",
      "AI explains fit and scopes roles. It never ranks applicants and never makes hiring decisions.",
      "Pay and legal rules (Living Wage, hour limits) are calculated by code, not by the AI.",
      "AI requests are processed through the Anthropic API under commercial terms, which do not use API data to train models by default.",
      "You can switch AI matching off in your Passport — we'll use a simple offline matcher instead.",
    ],
  },
  {
    icon: <ShieldCheck className="size-5" />,
    title: "Our commitments",
    items: [
      "We never sell, rent or share your data with advertisers or data brokers.",
      "Passwords are stored as salted PBKDF2 hashes; sessions use HttpOnly cookies that scripts can't read.",
      "You can export everything we hold about you, or delete your account, at any time.",
      "This is a hackathon prototype using synthetic data. A real launch needs legal review (UK GDPR, ICO guidance on B2B marketing).",
    ],
  },
];

export default function Trust() {
  const { user, clear } = useAuth();
  const [log, setLog] = useState<LogEntry[] | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) api.get<{ entries: LogEntry[] }>("/account/access-log").then((r) => setLog(r.entries)).catch(() => setLog([]));
  }, [user]);

  const remove = async () => {
    setDeleting(true);
    await api.del("/account");
    clear();
    navigate("/");
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
          <Link to="/"><Logo /></Link>
          <Link to={user ? homeFor(user.role) : "/"} className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-2 hover:text-ink">
            <ArrowLeft className="size-4" /> Back
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-good"><ShieldCheck className="size-4" /> Privacy & trust centre</span>
        <h1 className="mt-2 text-3xl font-extrabold sm:text-4xl">Your data works for you — and only inside FirstHire.</h1>
        <p className="mt-3 max-w-3xl text-lg text-ink-2">
          FirstHire is an internal matching system between local graduates and local firms. Here is exactly what we hold, who sees it, and what the AI does with it.
        </p>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {SECTIONS.map((s) => (
            <Card key={s.title} className="p-6">
              <div className="flex items-center gap-3">
                <span className="rounded-xl bg-good-soft p-2.5 text-good">{s.icon}</span>
                <h2 className="text-lg font-bold">{s.title}</h2>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-ink-2">
                {s.items.map((i) => <li key={i} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-good" />{i}</li>)}
              </ul>
            </Card>
          ))}
        </div>

        {user && (
          <section className="mt-10">
            <h2 className="text-2xl font-extrabold">Your data controls</h2>
            <div className="mt-5 grid gap-5 lg:grid-cols-[1.4fr_1fr]">
              <Card className="p-6">
                <div className="flex items-center gap-2"><History className="size-5 text-brand" /><h3 className="font-bold">Access log</h3></div>
                <p className="mt-1 text-sm text-ink-2">Every time a firm or the AI touched your data.</p>
                <div className="mt-4 divide-y divide-line">
                  {log === null && <p className="py-3 text-sm text-ink-3">Loading…</p>}
                  {log?.length === 0 && <p className="py-3 text-sm text-ink-3">Nothing yet — nobody has accessed your data.</p>}
                  {log?.map((e, i) => (
                    <div key={i} className="flex items-start justify-between gap-4 py-3 text-sm">
                      <div>
                        <div className="font-semibold">{e.actor}</div>
                        <div className="text-ink-2">{e.action}</div>
                        {e.detail && <div className="text-xs text-ink-3">{e.detail}</div>}
                      </div>
                      <div className="shrink-0 text-xs text-ink-3">{dateLabel(e.created_at)}</div>
                    </div>
                  ))}
                </div>
              </Card>
              <div className="space-y-5">
                <Card className="p-6">
                  <h3 className="font-bold">Download my data</h3>
                  <p className="mt-1 text-sm text-ink-2">A JSON file with everything we hold about you, including what the AI sees.</p>
                  <a href="/api/account/export" download className="mt-4 inline-flex h-10 items-center gap-2 rounded-lg border border-line bg-surface px-4 text-sm font-semibold hover:bg-surface-2">
                    <Download className="size-4" /> Export (JSON)
                  </a>
                </Card>
                <Card className="p-6">
                  <h3 className="font-bold">Delete my account</h3>
                  <p className="mt-1 text-sm text-ink-2">Permanently removes your account, Passport, applications and access log.</p>
                  <Button variant="danger" className="mt-4" icon={<Trash2 className="size-4" />} onClick={() => setConfirm(true)}>Delete account</Button>
                </Card>
              </div>
            </div>
          </section>
        )}
      </main>

      <Modal open={confirm} onClose={() => setConfirm(false)} title="Delete your account?">
        <Alert tone="bad">This permanently deletes your account and personal data. It can't be undone. (In the demo, re-running the seed script restores it.)</Alert>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setConfirm(false)}>Cancel</Button>
          <Button variant="danger" loading={deleting} onClick={remove}>Yes, delete everything</Button>
        </div>
      </Modal>
    </div>
  );
}
