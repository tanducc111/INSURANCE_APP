import type { LucideIcon } from "lucide-react";

type KpiCardProps = {
  label: string;
  value: number | string;
  helper?: string;
  icon?: LucideIcon;
  tone?: "blue" | "cyan" | "green" | "amber" | "red";
};

const tones = {
  amber: "bg-amber-50 text-amber-700 ring-amber-100",
  blue: "bg-blue-50 text-blue-700 ring-blue-100",
  cyan: "bg-cyan-50 text-cyan-700 ring-cyan-100",
  green: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  red: "bg-red-50 text-red-700 ring-red-100",
};

export function KpiCard({
  helper,
  icon: Icon,
  label,
  tone = "blue",
  value,
}: KpiCardProps) {
  return (
    <article className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-muted">{label}</p>
          <p className="mt-3 text-3xl font-extrabold text-ink">{value}</p>
        </div>
        {Icon ? (
          <span className={`rounded-lg p-2 ring-1 ${tones[tone]}`}>
            <Icon aria-hidden className="h-5 w-5" />
          </span>
        ) : null}
      </div>
      {helper ? <p className="mt-4 text-sm text-muted">{helper}</p> : null}
    </article>
  );
}
