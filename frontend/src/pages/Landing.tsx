import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, BadgeCheck, Ban, Building2, EyeOff, GraduationCap, HandCoins, Lightbulb, Lock, MapPin, ScanSearch,
  Sparkles, Trash2, UserCheck,
} from "lucide-react";
import { Logo } from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth, homeFor } from "../lib/auth";
import { ThemeToggle } from "../components/ThemeToggle";

type Stats = { firms: number; open_opportunities: number; towns: number; graduates: number };

const PROMISES = [
  { icon: <Ban className="size-5" />, title: "Your data is never sold", text: "No advertisers, no data brokers. Your information only powers matching inside FirstHire." },
  { icon: <EyeOff className="size-5" />, title: "Blind first review", text: "Firms see your answer and skills first — your name, photo and university stay hidden until they invite you to interview." },
  { icon: <UserCheck className="size-5" />, title: "People decide, not AI", text: "AI helps scope roles and explain fit. It never ranks applicants. Owners make every hiring decision." },
  { icon: <HandCoins className="size-5" />, title: "Always paid, fairly", text: "Every opportunity pays at least the National Living Wage. Code checks the pay — no unpaid “experience”." },
  { icon: <ScanSearch className="size-5" />, title: "See what the AI sees", text: "Graduates can preview the exact anonymised profile our AI receives, and switch AI matching off." },
  { icon: <Trash2 className="size-5" />, title: "Export or delete anytime", text: "Download everything we hold about you, see who accessed it, or delete your account in one click." },
];

export default function Landing() {
  const [stats, setStats] = useState<Stats | null>(null);
  const { user } = useAuth();
  useEffect(() => { api.get<Stats>("/public/stats").then(setStats).catch(() => undefined); }, []);
  const cta = user ? homeFor(user.role) : "/login";

  return (
    <div className="bg-bg">
      {/* Nav */}
      <header className="absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <Logo light />
          <nav className="hidden items-center gap-7 text-sm font-medium text-white/80 md:flex">
            <a href="#how" className="hover:text-white">How it works</a>
            <a href="#trust" className="hover:text-white">Trust</a>
            <Link to="/trust" className="hover:text-white">Privacy</Link>
          </nav>
          <div className="flex items-center gap-3">
            <ThemeToggle onDark />
            <Link to={cta} className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-[#0b1f3a] hover:bg-white/90">
              {user ? "Open dashboard" : "Sign in"}
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-navy pt-28 pb-20 text-white sm:pt-36 sm:pb-28">
        <div aria-hidden className="pointer-events-none absolute -top-40 right-[-10%] size-[640px] rounded-full bg-[radial-gradient(circle,rgba(91,140,255,0.35),transparent_65%)]" />
        <div aria-hidden className="pointer-events-none absolute bottom-[-30%] left-[-10%] size-[520px] rounded-full bg-[radial-gradient(circle,rgba(245,184,61,0.18),transparent_65%)]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="animate-rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-3 py-1 text-xs font-semibold text-white/80">
              <MapPin className="size-3.5 text-gold" /> Newcastle · Gateshead · Sunderland · Durham
            </span>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.08] sm:text-6xl">
              Your first job is <span className="text-gold">closer than London.</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg text-white/75">
              FirstHire helps small North East firms turn real business problems into paid first opportunities — and matches them with local graduates using AI that explains every suggestion.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/login?as=graduate" className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-gold px-6 font-semibold text-navy hover:brightness-105">
                <GraduationCap className="size-5" /> I'm a graduate
              </Link>
              <Link to="/login?as=owner" className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-white/25 bg-white/5 px-6 font-semibold text-white hover:bg-white/10">
                <Building2 className="size-5" /> I run a business
              </Link>
            </div>
            <p className="mt-5 flex items-center gap-2 text-sm text-white/60"><Lock className="size-4" /> Free to use for graduates and businesses. Firms only pay the graduate's wage.</p>
          </div>

          {/* Product preview */}
          <div className="relative hidden pb-36 lg:block" aria-hidden>
            <div className="rotate-[-2deg] rounded-2xl bg-white p-5 text-ink shadow-2xl">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-[#5f6573]">Paid project · 8 weeks</div>
                  <div className="mt-1 font-display text-lg font-bold text-[#0f1b2d]">Website & online ordering build</div>
                  <div className="text-sm text-[#475467]">Tyne Street Kitchen · Gateshead · 0.8 mi</div>
                </div>
                <div className="grid size-14 place-items-center rounded-full border-4 border-[#2a78d6] font-display text-lg font-extrabold text-[#0f1b2d]">86</div>
              </div>
              <div className="mt-4 rounded-xl bg-[#f2ecff] p-3 text-sm text-[#3b2491]">
                <div className="mb-1 flex items-center gap-1.5 font-semibold"><Sparkles className="size-4" /> Why it fits you</div>
                Your React project and weekend café shifts mean you understand both the code and the lunchtime queue.
              </div>
              <div className="mt-3 flex gap-2 text-xs">
                <span className="rounded-full bg-[#e5f5eb] px-2 py-0.5 font-semibold text-[#157a3c]">£12.71/h · checked</span>
                <span className="rounded-full bg-[#f0f3f7] px-2 py-0.5 font-semibold text-[#475467]">15 h/week</span>
              </div>
            </div>
            <div className="absolute bottom-0 -left-8 w-72 rotate-[3deg] rounded-2xl bg-white p-4 text-[#0f1b2d] shadow-2xl">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#6d3fd8]"><Lightbulb className="size-4" /> Growth Advisor</div>
              <div className="mt-1 text-sm font-semibold">640 five-star reviews, but no website.</div>
              <div className="mt-1 text-xs text-[#475467]">Suggest a paid 8-week student project? Est. £1,709 incl. holiday pay.</div>
            </div>
          </div>
        </div>
      </section>

      {/* Evidence strip */}
      <section className="border-b border-line bg-surface">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-4 py-10 sm:px-6 lg:grid-cols-4">
          {[
            ["85%", "of students from outside the region leave after graduating"],
            ["65%", "of full-time undergraduates already work during term"],
            ["~15,000", "North East firms with 5–49 staff — most never hired a graduate"],
            [stats ? `${stats.open_opportunities}` : "—", `paid, local opportunities open now across ${stats?.towns ?? "—"} towns`],
          ].map(([n, t]) => (
            <div key={t}>
              <div className="font-display text-3xl font-extrabold text-brand">{n}</div>
              <div className="mt-1 text-sm text-ink-2">{t}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <h2 className="text-center text-3xl font-extrabold">One loop. Two AI agents. Real local work.</h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-ink-2">The firm's problem becomes the graduate's opportunity — scoped by AI, approved by people, paid properly.</p>
        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {[
            {
              icon: <Building2 className="size-5" />, who: "For business owners", tone: "text-ai bg-ai-soft",
              steps: [
                ["Tell the Growth Advisor what's not working", "Or let it spot gaps from your data — like great reviews but no website."],
                ["Get a fair, scoped opportunity", "Tasks, a 12-week plan, skills — with unnecessary requirements removed. Code calculates the cost."],
                ["Review applicants blind", "Evidence first, identity at interview. You choose; a mentor supports the work."],
              ],
            },
            {
              icon: <GraduationCap className="size-5" />, who: "For graduates", tone: "text-brand bg-brand-soft",
              steps: [
                ["Build one Passport", "Upload your CV — AI drafts your profile. Part-time jobs count as real experience."],
                ["Discover local matches", "Only roles within your travel radius, each with a clear “why it fits” and a local career path."],
                ["Apply with one real answer", "One role-specific question, a monthly limit for quality, and live status tracking."],
              ],
            },
          ].map((col) => (
            <div key={col.who} className="rounded-2xl border border-line bg-surface p-7 shadow-card">
              <div className="flex items-center gap-3">
                <span className={`rounded-xl p-2.5 ${col.tone}`}>{col.icon}</span>
                <h3 className="text-xl font-bold">{col.who}</h3>
              </div>
              <ol className="mt-6 space-y-5">
                {col.steps.map(([t, d], i) => (
                  <li key={t} className="flex gap-4">
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-2 font-display text-sm font-bold text-ink-2">{i + 1}</span>
                    <div>
                      <div className="font-semibold">{t}</div>
                      <div className="text-sm text-ink-2">{d}</div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </section>

      {/* Trust */}
      <section id="trust" className="border-y border-line bg-surface">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
            <div>
              <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-good"><BadgeCheck className="size-4" /> Our promises</span>
              <h2 className="mt-2 text-3xl font-extrabold">Built so both sides can trust it</h2>
              <p className="mt-2 max-w-2xl text-ink-2">Your data is used only inside this internal matching system — never sold, never used for advertising.</p>
            </div>
            <Link to="/trust" className="inline-flex items-center gap-1.5 font-semibold text-brand hover:underline">Read the full privacy & trust centre <ArrowRight className="size-4" /></Link>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {PROMISES.map((p) => (
              <div key={p.title} className="rounded-2xl border border-line bg-bg p-6">
                <span className="inline-flex rounded-xl bg-good-soft p-2.5 text-good">{p.icon}</span>
                <h3 className="mt-4 font-bold">{p.title}</h3>
                <p className="mt-1 text-sm text-ink-2">{p.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6">
        <h2 className="text-3xl font-extrabold">Build your career where you studied.</h2>
        <p className="mx-auto mt-3 max-w-xl text-ink-2">Join the local loop — paid projects, internships and first jobs with North East firms.</p>
        <Link to={cta} className="mt-8 inline-flex h-12 items-center gap-2 rounded-xl bg-brand px-6 font-semibold text-brand-ink hover:bg-brand-hover">
          Get started <ArrowRight className="size-4" />
        </Link>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-ink-3 sm:flex-row sm:px-6">
          <Logo />
          <span>Hackathon prototype · all firms and people shown are synthetic.</span>
        </div>
      </footer>
    </div>
  );
}
