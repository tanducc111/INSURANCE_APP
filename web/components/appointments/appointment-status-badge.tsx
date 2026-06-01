import { StatusBadge } from "@/components/ui/status-badge";
import type { AppointmentStatus } from "@/types/communication";

export function AppointmentStatusBadge({
  status,
}: {
  status: AppointmentStatus;
}) {
  return <StatusBadge value={status} />;
}
