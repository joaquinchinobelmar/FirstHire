import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { LogOut, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { useAuth } from "../lib/auth";
import { cx } from "./ui";
import { ThemeToggle } from "./ThemeToggle";

export function Logo({ light }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <svg viewBox="0 0 32 32" className="size-8" aria-hidden>
        <rect width="32" height="32" rx="8" fill="var(--brand)" />
        <path d="M9 23V9h12v3.2h-8.4v2.6h7.4V18h-7.4v5z" fill="#fff" />
        <circle cx="23" cy="21.5" r="2.5" fill="var(--gold)" />
      </svg>
      <span className={cx("font-display text-lg font-extrabold", light ? "text-white" : "text-ink")}>FirstHire</span>
    </span>
  );
}

export type Tab = { to: string; label: string; icon: ReactNode };

export function AppShell({ tabs, areaLabel }: { tabs: Tab[]; areaLabel: string }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" aria-label="FirstHire home"><Logo /></Link>
          <span className="hidden rounded-md bg-surface-2 px-2 py-1 text-xs font-semibold text-ink-2 sm:inline">{areaLabel}</span>
          <nav className="ml-4 hidden gap-1 md:flex" aria-label="Sections">
            {tabs.map((t) => (
              <NavLink key={t.to} to={t.to} className={({ isActive }) => cx("flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors", isActive ? "bg-brand-soft text-brand" : "text-ink-2 hover:bg-surface-2 hover:text-ink")}>
                {t.icon}
                {t.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle className="mr-1" />
            <NavLink to="/trust" className="hidden items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-ink-2 hover:bg-surface-2 sm:flex">
              <ShieldCheck className="size-4 text-good" /> Privacy & trust
            </NavLink>
            <div className="hidden text-right leading-tight sm:block">
              <div className="text-sm font-semibold">{user?.name}</div>
              <div className="text-xs text-ink-3">{user?.role === "graduate" ? "Graduate" : "Business owner"}</div>
            </div>
            <button
              onClick={async () => { await logout(); navigate("/login"); }}
              className="cursor-pointer rounded-lg p-2 text-ink-3 hover:bg-surface-2 hover:text-ink"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className="size-5" />
            </button>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto border-t border-line px-3 py-2 md:hidden" aria-label="Sections">
          {tabs.map((t) => (
            <NavLink key={t.to} to={t.to} className={({ isActive }) => cx("flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold", isActive ? "bg-brand-soft text-brand" : "text-ink-2")}>
              {t.icon}
              {t.label}
            </NavLink>
          ))}
          <NavLink to="/trust" className="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold text-ink-2">
            <ShieldCheck className="size-4" /> Trust
          </NavLink>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
