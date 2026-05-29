import type { ClaimStatus } from "@/types/claim";

const statusStyles: Record<ClaimStatus, string> = {
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  reviewing: "border-blue-200 bg-blue-50 text-blue-700",
  need_more_documents: "border-orange-200 bg-orange-50 text-orange-700",
  approved: "border-emerald-200 bg-emerald-50 text-emerald-700",
  rejected: "border-red-200 bg-red-50 text-red-700",
  completed: "border-slate-200 bg-slate-100 text-slate-700",
};

export function formatClaimLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function ClaimStatusBadge({ status }: { status: ClaimStatus }) {
  return (
    <span
      className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-semibold capitalize ${statusStyles[status]}`}
    >
      {formatClaimLabel(status)}
    </span>
  );
}
