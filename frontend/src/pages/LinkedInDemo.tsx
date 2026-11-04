import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { FlaskConical } from "lucide-react";
import { Alert, Button, Field, Input } from "../components/ui";
import { LinkedInMark } from "../components/LinkedInButton";
import { ThemeToggle } from "../components/ThemeToggle";

/**
 * Demo-mode stand-in for LinkedIn's consent screen, used only when the server has no
 * LinkedIn app keys. It produces the same profile shape (name + email) the real
 * OpenID Connect flow returns, so the rest of the sign-up path is exercised for real.
 */
const b64url = (s: string) => btoa(unescape(encodeURIComponent(s))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

export default function LinkedInDemo() {
  const [params] = useSearchParams();
  const state = params.get("state") ?? "";
  const [name, setName] = useState("Jordan Reid");
  const [email, setEmail] = useState("jordan.reid@student.example");

  const callback = (query: string) => `/api/auth/linkedin/callback?${query}&state=${encodeURIComponent(state)}`;
  const allow = (e: FormEvent) => {
    e.preventDefault();
    window.location.href = callback(`code=demo.${b64url(JSON.stringify({ name, email }))}`);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-bg px-4 py-12">
      <ThemeToggle className="absolute right-4 top-4" />
      <div className="w-full max-w-md">
        <Alert tone="warn" icon={<FlaskConical className="size-4" />} className="mb-4">
          <b>Simulated LinkedIn sign-in (demo mode).</b> This server has no LinkedIn app keys yet, so this local page stands in for LinkedIn's consent screen. Add
          <code className="mx-1">LINKEDIN_CLIENT_ID</code>/<code className="mx-1">LINKEDIN_CLIENT_SECRET</code> to use the real thing.
        </Alert>
        <div className="rounded-2xl border border-line bg-surface p-7 shadow-card">
          <div className="flex items-center gap-2 text-[#0a66c2]"><LinkedInMark className="size-7" /><span className="font-display text-lg font-bold text-ink">FirstHire wants to:</span></div>
          <ul className="mt-4 space-y-2 text-sm text-ink-2">
            <li>• Use your name and email address to create your account</li>
            <li className="text-ink-3">• It will <b>not</b> post for you, see your connections or store your photo</li>
          </ul>
          <form onSubmit={allow} className="mt-6 space-y-4">
            <Field label="Name on LinkedIn"><Input value={name} onChange={(e) => setName(e.target.value)} required /></Field>
            <Field label="Primary email"><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></Field>
            <div className="flex gap-2 pt-1">
              <Button type="button" variant="secondary" className="flex-1" onClick={() => (window.location.href = callback("error=user_cancelled_login"))}>Cancel</Button>
              <Button type="submit" className="flex-1 !bg-[#0a66c2] !text-white hover:!bg-[#004182]">Allow</Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
