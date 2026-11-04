export const BRAND = { name: "FirstHire", tagline: "Local first jobs for North East graduates" };

export const gbp = (n: number, digits = 0) =>
  new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: digits, minimumFractionDigits: digits }).format(n);

export const pct = (n: number) => `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;

export const monthLabel = (ym: string) => {
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
};

export const dateLabel = (iso: string) => {
  const d = new Date(iso.replace(" ", "T") + (iso.includes("Z") || iso.includes("+") ? "" : "Z"));
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
};

export const distanceLabel = (miles: number | null, town: string) =>
  miles == null ? town : miles < 1 ? `In ${town}` : `${town} · ${miles} mi`;

export const durationLabel = (weeks: number | null) => (weeks ? `${weeks} weeks` : "Permanent");

export const STATUS_LABEL: Record<string, string> = {
  submitted: "Submitted",
  shortlisted: "Shortlisted",
  interview: "Interview",
  offered: "Offer",
  rejected: "Not progressed",
  withdrawn: "Withdrawn",
};
