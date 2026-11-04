import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, ChevronDown, ClipboardList, MessageSquareQuote, Undo2 } from "lucide-react";
import { OppFacts, TypeBadge } from "../../components/OpportunityBits";
import { Alert, Badge, Button, Card, EmptyState, PageHeader, Spinner, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { STATUS_LABEL, dateLabel } from "../../lib/format";
import type { StudentApplication } from "../../lib/types";

type Resp = { applications: StudentApplication[]; flow: string[]; applications_this_month: number; monthly_limit: number };

const toneFor = (s: string) => (s === "offered" ? "good" : s === "interview" ? "brand" : s === "shortlisted" ? "ai" : s === "rejected" ? "bad" : "neutral") as "good" | "brand" | "ai" | "bad" | "neutral";

function Stepper({ flow, status }: { flow: string[]; status: string }) {
  const closed = status === "rejected" || status === "withdrawn";
  const reached = closed ? -1 : flow.indexOf(status);
  return (
    <ol className="flex items-center" aria-label="Application progress">
      {flow.map((step, i) => {
        const done = i <= reached;
        return (
          <li key={step} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <span className={cx("grid size-7 place-items-center rounded-full border-2 text-xs font-bold", done ? "border-brand bg-brand text-brand-ink" : "border-line bg-surface text-ink-3")}>
                {done ? <Check className="size-3.5" /> : i + 1}
              </span>
              <span className={cx("text-[11px] font-semibold", done ? "text-ink" : "text-ink-3")}>{STATUS_LABEL[step]}</span>
            </div>
            {i < flow.length - 1 && <span className={cx("mx-1 mb-5 h-0.5 flex-1 rounded", i < reached ? "bg-brand" : "bg-line")} />}
          </li>
        );
      })}
    </ol>
  );
}

function AppCard({ a, flow, onWithdraw }: { a: StudentApplication; flow: string[]; onWithdraw: () => void }) {
  const [open, setOpen] = useState(false);
  const latest = a.events[a.events.length - 1];
  const closed = ["rejected", "withdrawn", "offered"].includes(a.status);
  return (
    <Card className="p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <TypeBadge label={a.opportunity.type_label} />
            <Badge tone={toneFor(a.status)}>{STATUS_LABEL[a.status] ?? a.status}</Badge>
            <span className="text-xs text-ink-3">Applied {dateLabel(a.created_at)}</span>
          </div>
          <h3 className="mt-2 text-lg font-bold">{a.opportunity.title}</h3>
          <div className="mb-2 text-sm text-ink-2">{a.opportunity.firm.name}</div>
          <OppFacts o={a.opportunity} />
        </div>
        <div className="w-full lg:w-[380px]">
          {a.status === "rejected" || a.status === "withdrawn" ? (
            <div className="rounded-xl bg-surface-2 p-3 text-sm text-ink-2">{a.status === "withdrawn" ? "You withdrew this application." : "This one didn't work out — every application builds your Passport."}</div>
          ) : (
            <Stepper flow={flow} status={a.status} />
          )}
        </div>
      </div>

      {latest && (
        <div className={cx("mt-4 flex gap-3 rounded-xl p-3 text-sm", a.status === "interview" || a.status === "offered" ? "bg-brand-soft" : "bg-surface-2")}>
          <MessageSquareQuote className="mt-0.5 size-4 shrink-0 text-ink-3" />
          <div><span className="font-semibold">Latest update · {dateLabel(latest.created_at)}: </span>{latest.note}</div>
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <button onClick={() => setOpen((v) => !v)} className="inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-brand">
          {open ? "Hide" : "Show"} timeline & my answer <ChevronDown className={cx("size-4 transition-transform", open && "rotate-180")} />
        </button>
        {!closed && <Button variant="ghost" size="sm" icon={<Undo2 className="size-4" />} onClick={onWithdraw}>Withdraw</Button>}
      </div>
      {open && (
        <div className="mt-4 grid gap-5 border-t border-line pt-4 md:grid-cols-2">
          <ol className="space-y-3">
            {a.events.map((e, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="mt-1.5 size-2 shrink-0 rounded-full bg-brand" />
                <div><div className="font-semibold">{STATUS_LABEL[e.status] ?? e.status} <span className="font-normal text-ink-3">· {dateLabel(e.created_at)}</span></div><div className="text-ink-2">{e.note}</div></div>
              </li>
            ))}
          </ol>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-3">{a.opportunity.role_question}</div>
            <p className="mt-1 whitespace-pre-line text-sm">{a.answer}</p>
          </div>
        </div>
      )}
    </Card>
  );
}

export default function Applications() {
  const [data, setData] = useState<Resp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () => api.get<Resp>("/student/applications").then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner label="Loading your applications…" />;

  const count = (s: string[]) => data.applications.filter((a) => s.includes(a.status)).length;
  const tiles = [
    ["Active", count(["submitted", "shortlisted", "interview"])],
    ["Interviews", count(["interview"])],
    ["Offers", count(["offered"])],
    ["This month", `${data.applications_this_month}/${data.monthly_limit}`],
  ] as const;

  return (
    <div>
      <PageHeader title="My applications" subtitle="Follow every application in real time. Firms are asked to give every applicant a fair first review." />
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {tiles.map(([label, value]) => (
          <Card key={label} className="p-5">
            <div className="text-sm font-medium text-ink-2">{label}</div>
            <div className="mt-1 font-display text-3xl font-extrabold">{value}</div>
          </Card>
        ))}
      </div>
      {data.applications.length === 0 ? (
        <EmptyState icon={<ClipboardList className="size-6" />} title="No applications yet">
          <Link to="/graduate/opportunities" className="font-semibold text-brand">Discover local opportunities</Link> that match your Passport.
        </EmptyState>
      ) : (
        <div className="space-y-4">
          {data.applications.map((a) => (
            <AppCard key={a.id} a={a} flow={data.flow} onWithdraw={async () => { await api.post(`/student/applications/${a.id}/withdraw`); load(); }} />
          ))}
        </div>
      )}
    </div>
  );
}
