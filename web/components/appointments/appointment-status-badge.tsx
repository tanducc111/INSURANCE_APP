import type { AppointmentStatus } from "@/types/communication";

const statusStyles: Record<AppointmentStatus, string> = {
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  accepted: "border-emerald-200 bg-emerald-50 text-emerald-700",
  rejected: "border-red-200 bg-red-50 text-red-700",
  rescheduled: "border-blue-200 bg-blue-50 text-blue-700",
  cancelled: "border-slate-200 bg-slate-100 text-slate-700",
  completed: "border-teal-200 bg-teal-50 text-teal-700",
};

export function AppointmentStatusBadge({
  status,
}: {
  status: AppointmentStatus;
}) {
  return (
    <span
      className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-semibold capitalize ${statusStyles[status]}`}
    >
      {status}
    </span>
  );
}
