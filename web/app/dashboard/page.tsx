"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  BriefcaseBusiness,
  CalendarCheck2,
  ClipboardList,
  FileCheck2,
  PackageCheck,
  UsersRound,
} from "lucide-react";

import { ChartCard } from "@/components/ui/chart-card";
import { EmptyState } from "@/components/ui/empty-state";
import { KpiCard } from "@/components/ui/kpi-card";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge, statusLabel } from "@/components/ui/status-badge";
import { getStoredToken, getStoredUser } from "@/lib/auth-storage";
import { ApiError } from "@/services/api-client";
import {
  getAdminDashboard,
  getCustomerDashboard,
  getEmployeeDashboard,
} from "@/services/subscription-service";
import type { UserRole } from "@/types/auth";
import type {
  AdminDashboardStats,
  CustomerDashboardStats,
  EmployeeDashboardStats,
} from "@/types/subscription";

const chartColors = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444"];

export default function DashboardPage() {
  const [role, setRole] = useState<UserRole | null>(null);
  const [adminStats, setAdminStats] = useState<AdminDashboardStats | null>(null);
  const [employeeStats, setEmployeeStats] =
    useState<EmployeeDashboardStats | null>(null);
  const [customerStats, setCustomerStats] =
    useState<CustomerDashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      const token = getStoredToken();
      const user = getStoredUser();
      if (!token || !user) {
        return;
      }

      setRole(user.role);
      setIsLoading(true);
      setError(null);
      try {
        if (user.role === "ADMIN") {
          setAdminStats(await getAdminDashboard(token));
        } else if (user.role === "EMPLOYEE") {
          setEmployeeStats(await getEmployeeDashboard(token));
        } else {
          setCustomerStats(await getCustomerDashboard(token));
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Không thể tải bảng điều khiển",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const subscriptionChart = useMemo(
    () =>
      adminStats?.subscription_status_chart.map((item) => ({
        ...item,
        label: statusLabel(item.label),
      })) ?? [],
    [adminStats],
  );

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
        {error}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        description="Theo dõi nhanh dữ liệu vận hành, hiệu suất xử lý và tình trạng hợp đồng theo từng vai trò."
        eyebrow="Tổng quan"
        title="Bảng điều khiển"
      />

      {role === "ADMIN" && adminStats ? (
        <section className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              icon={UsersRound}
              label="Tổng khách hàng"
              value={adminStats.total_customers}
            />
            <KpiCard
              icon={BriefcaseBusiness}
              label="Tổng nhân viên"
              tone="cyan"
              value={adminStats.total_employees}
            />
            <KpiCard
              icon={PackageCheck}
              label="Gói bảo hiểm"
              tone="green"
              value={adminStats.total_packages}
            />
            <KpiCard
              icon={FileCheck2}
              label="Hợp đồng hiệu lực"
              tone="green"
              value={adminStats.active_subscriptions}
            />
            <KpiCard
              icon={FileCheck2}
              label="Hợp đồng chờ xử lý"
              tone="amber"
              value={adminStats.pending_subscriptions}
            />
            <KpiCard
              icon={ClipboardList}
              label="Bồi thường đang mở"
              tone="amber"
              value={adminStats.open_claims}
            />
            <KpiCard
              icon={ClipboardList}
              label="Bồi thường đã duyệt"
              tone="green"
              value={adminStats.approved_claims}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <ChartCard
              description="Tỷ trọng hợp đồng theo từng trạng thái nghiệp vụ."
              title="Trạng thái hợp đồng"
            >
              {subscriptionChart.length === 0 ? (
                <EmptyState title="Chưa có dữ liệu biểu đồ" />
              ) : (
                <div className="h-72">
                  <ResponsiveContainer height="100%" width="100%">
                    <PieChart>
                      <Pie
                        data={subscriptionChart}
                        dataKey="value"
                        innerRadius={58}
                        nameKey="label"
                        outerRadius={96}
                      >
                        {subscriptionChart.map((entry, index) => (
                          <Cell
                            fill={chartColors[index % chartColors.length]}
                            key={entry.label}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>

            <ChartCard
              description="Số lượt đăng ký theo từng gói bảo hiểm."
              title="Đăng ký theo gói"
            >
              {adminStats.package_registration_chart.length === 0 ? (
                <EmptyState title="Chưa có dữ liệu biểu đồ" />
              ) : (
                <div className="h-72">
                  <ResponsiveContainer height="100%" width="100%">
                    <BarChart data={adminStats.package_registration_chart}>
                      <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" />
                      <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#2563EB" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>
          </div>
        </section>
      ) : null}

      {role === "EMPLOYEE" && employeeStats ? (
        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            icon={UsersRound}
            label="Khách hàng được phân công"
            value={employeeStats.assigned_customers_count}
          />
          <KpiCard
            icon={FileCheck2}
            label="Hợp đồng hiệu lực"
            tone="green"
            value={employeeStats.active_subscriptions_count}
          />
          <KpiCard
            icon={CalendarCheck2}
            label="Công việc cần theo dõi"
            tone="amber"
            value={employeeStats.pending_follow_ups}
          />
          <KpiCard
            icon={ClipboardList}
            label="Bồi thường chờ xử lý"
            tone="red"
            value={employeeStats.open_claims_count}
          />
        </section>
      ) : null}

      {role === "CUSTOMER" && customerStats ? (
        <section className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              icon={FileCheck2}
              label="Hợp đồng đang hiệu lực"
              tone="green"
              value={customerStats.active_packages}
            />
            <KpiCard
              icon={FileCheck2}
              label="Hợp đồng hết hạn"
              value={customerStats.expired_packages}
            />
            <KpiCard
              icon={ClipboardList}
              label="Hồ sơ bồi thường"
              tone="amber"
              value={customerStats.open_claims}
            />
            <KpiCard
              icon={BriefcaseBusiness}
              label="Nhân viên phụ trách"
              value={customerStats.assigned_employee?.full_name ?? "Chưa phân công"}
            />
          </div>

          <ChartCard title="Hợp đồng gần đây">
            {customerStats.latest_subscriptions.length === 0 ? (
              <EmptyState
                description="Khi hợp đồng được phát hành, danh sách mới nhất sẽ hiển thị tại đây."
                title="Chưa có hợp đồng"
              />
            ) : (
              <div className="divide-y divide-border">
                {customerStats.latest_subscriptions.map((subscription) => (
                  <div
                    className="flex flex-col gap-3 py-4 md:flex-row md:items-center md:justify-between"
                    key={subscription.id}
                  >
                    <div>
                      <p className="font-bold text-ink">
                        {subscription.package_name}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        Số hợp đồng: {subscription.policy_number}
                      </p>
                    </div>
                    <StatusBadge value={subscription.status} />
                  </div>
                ))}
              </div>
            )}
          </ChartCard>
        </section>
      ) : null}
    </div>
  );
}
