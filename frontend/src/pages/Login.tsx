import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Building2, GraduationCap, Lock, ShieldCheck } from "lucide-react";
import { Logo } from "../components/AppShell";
import { Alert, Button, Field, Input, cx } from "../components/ui";
import { homeFor, useAuth } from "../lib/auth";

export default function Login() {
  const [params] = useSearchParams();
  const [as, setAs] = useState<"graduate" | "owner">(params.get("as") === "owner" ? "owner" : "graduate");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { user, login } = useAuth();
  const navigate = useNavigate();

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const u = await login(email, password);
      navigate(homeFor(u.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden bg-navy p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div aria-hidden className="absolute -right-32 -top-32 size-[520px] rounded-full bg-[radial-gradient(circle,rgba(91,140,255,0.35),transparent_65%)]" />
        <Link to="/" className="relative"><Logo light /></Link>
        <div className="relative">
          <h2 className="text-4xl font-extrabold leading-tight">
            {as === "graduate" ? "Local opportunities that fit your life — and your skills." : "Turn the work piling up into your first great hire."}
          </h2>
          <ul className="mt-8 space-y-3 text-white/80">
            {(as === "graduate"
              ? ["Matches only within your travel radius", "Blind first review — skills before names", "Every role paid at least the Living Wage"]
              : ["AI spots gaps and scopes a fair role", "Code calculates the full cost before you commit", "Review applicants on evidence, not CV gloss"]
            ).map((t) => (
              <li key={t} className="flex items-center gap-3"><ShieldCheck className="size-5 text-gold" /> {t}</li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-white/50">Your data stays inside FirstHire. It is never sold or used for advertising.</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Link to="/" className="mb-8 inline-block lg:hidden"><Logo /></Link>
          <h1 className="text-3xl font-extrabold">Sign in</h1>
          <p className="mt-1 text-ink-2">We'll take you to the right workspace for your account.</p>

          <div className="mt-6 grid grid-cols-2 gap-2 rounded-xl bg-surface-2 p-1" role="tablist">
            {([["graduate", "Graduate", GraduationCap], ["owner", "Business owner", Building2]] as const).map(([value, label, Icon]) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={as === value}
                onClick={() => setAs(value)}
                className={cx("flex cursor-pointer items-center justify-center gap-2 rounded-lg py-2 text-sm font-semibold transition-colors", as === value ? "bg-surface text-ink shadow-sm" : "text-ink-3 hover:text-ink")}
              >
                <Icon className="size-4" /> {label}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <Field label="Email">
              <Input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder={as === "graduate" ? "you@student.example" : "you@yourbusiness.example"} />
            </Field>
            <Field label="Password">
              <Input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            {error && <Alert tone="bad">{error}</Alert>}
            <Button type="submit" size="lg" className="w-full" loading={busy} icon={<Lock className="size-4" />}>Sign in securely</Button>
          </form>

          <p className="mt-6 text-center text-xs text-ink-3">
            Hackathon prototype — demo accounts are shared privately by the team. Passwords are stored as salted hashes and sessions use secure, HttpOnly cookies.
          </p>
        </div>
      </main>
    </div>
  );
}
