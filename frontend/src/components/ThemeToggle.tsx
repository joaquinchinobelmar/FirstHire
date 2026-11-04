import { Moon, Sun } from "lucide-react";
import { useTheme } from "../lib/theme";
import { cx } from "./ui";

/** Light / dark switch. `onDark` is for placements over the always-navy hero and login panel. */
export function ThemeToggle({ onDark, className }: { onDark?: boolean; className?: string }) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Light theme" : "Dark theme"}
      onClick={toggle}
      className={cx(
        "relative inline-flex h-8 w-[60px] shrink-0 cursor-pointer items-center rounded-full border transition-colors",
        onDark ? "border-white/25 bg-white/10 hover:bg-white/15" : "border-line bg-surface-2 hover:border-ink-3",
        className,
      )}
    >
      <Sun aria-hidden className={cx("absolute left-2 size-3.5", onDark ? "text-white/60" : "text-ink-3")} />
      <Moon aria-hidden className={cx("absolute right-2 size-3.5", onDark ? "text-white/60" : "text-ink-3")} />
      <span
        className={cx(
          "absolute top-[3px] grid size-6 place-items-center rounded-full shadow-sm transition-transform duration-200",
          onDark ? "bg-white text-navy" : "bg-surface text-ink ring-1 ring-line",
          isDark ? "translate-x-[30px]" : "translate-x-[3px]",
        )}
      >
        {isDark ? <Moon className="size-3.5" /> : <Sun className="size-3.5 text-[#b7791f]" />}
      </span>
    </button>
  );
}
