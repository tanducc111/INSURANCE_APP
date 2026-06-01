import type { AppointmentStatus } from "@/types/communication";
import type { ClaimIncidentType, ClaimPriority, ClaimStatus } from "@/types/claim";
import type { PaymentStatus, SubscriptionStatus } from "@/types/subscription";
import { viLabel } from "@/lib/vi-labels";

type KnownStatus =
  | ClaimStatus
  | ClaimIncidentType
  | ClaimPriority
  | AppointmentStatus
  | SubscriptionStatus
  | PaymentStatus
  | "active"
  | "inactive";

const styles: Record<string, string> = {
  accident: "border-orange-200 bg-orange-50 text-orange-700",
  active: "border-emerald-200 bg-emerald-50 text-emerald-700",
  accepted: "border-emerald-200 bg-emerald-50 text-emerald-700",
  approved: "border-emerald-200 bg-emerald-50 text-emerald-700",
  cancelled: "border-slate-200 bg-slate-100 text-slate-700",
  completed: "border-blue-200 bg-blue-50 text-blue-700",
  damage: "border-amber-200 bg-amber-50 text-amber-700",
  expired: "border-slate-200 bg-slate-100 text-slate-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  hospital: "border-sky-200 bg-sky-50 text-sky-700",
  inactive: "border-slate-200 bg-slate-100 text-slate-700",
  low: "border-slate-200 bg-slate-50 text-slate-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  need_more_documents: "border-amber-200 bg-amber-50 text-amber-700",
  other: "border-slate-200 bg-slate-50 text-slate-700",
  overdue: "border-red-200 bg-red-50 text-red-700",
  paid: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  rejected: "border-red-200 bg-red-50 text-red-700",
  rescheduled: "border-sky-200 bg-sky-50 text-sky-700",
  reviewing: "border-blue-200 bg-blue-50 text-blue-700",
  unpaid: "border-slate-200 bg-slate-50 text-slate-700",
  urgent: "border-red-200 bg-red-50 text-red-700",
};

export function statusLabel(value: string) {
  return viLabel(value);
}

export function StatusBadge({ value }: { value: KnownStatus | string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${
        styles[value] ?? "border-slate-200 bg-slate-50 text-slate-700"
      }`}
    >
      {statusLabel(value)}
    </span>
  );
}
