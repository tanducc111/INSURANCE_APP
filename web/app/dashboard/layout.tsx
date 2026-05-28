import { ProtectedDashboardShell } from "@/components/dashboard/protected-dashboard-shell";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <ProtectedDashboardShell>{children}</ProtectedDashboardShell>;
}
