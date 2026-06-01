import { StatusBadge, statusLabel } from "@/components/ui/status-badge";
import type { ClaimStatus } from "@/types/claim";

export function formatClaimLabel(value: string) {
  return statusLabel(value);
}

export function ClaimStatusBadge({ status }: { status: ClaimStatus }) {
  return <StatusBadge value={status} />;
}
