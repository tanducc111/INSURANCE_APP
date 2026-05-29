"use client";

import { useEffect, useState } from "react";
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

const chartColors = ["#0f766e", "#b7791f", "#3b82f6", "#64748b"];

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold">{value}</p>
    </div>
  );
}

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
        setError(err instanceof ApiError ? err.message : "Unable to load dashboard");
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (isLoading) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  if (error) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {error}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold">Overview</h1>
      </header>

      {role === "ADMIN" && adminStats ? (
        <section className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-7">
            <StatCard label="Customers" value={adminStats.total_customers} />
            <StatCard label="Employees" value={adminStats.total_employees} />
            <StatCard label="Packages" value={adminStats.total_packages} />
            <StatCard
              label="Active subs"
              value={adminStats.active_subscriptions}
            />
            <StatCard
              label="Pending subs"
              value={adminStats.pending_subscriptions}
            />
            <StatCard label="Open claims" value={adminStats.open_claims} />
            <StatCard label="Approved claims" value={adminStats.approved_claims} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Subscription Status</h2>
              {adminStats.subscription_status_chart.length === 0 ? (
                <p className="mt-5 text-sm font-medium text-slate-500">
                  No chart data available.
                </p>
              ) : (
                <div className="mt-5 h-72">
                  <ResponsiveContainer height="100%" width="100%">
                    <PieChart>
                      <Pie
                        data={adminStats.subscription_status_chart}
                        dataKey="value"
                        innerRadius={55}
                        nameKey="label"
                        outerRadius={95}
                      >
                        {adminStats.subscription_status_chart.map((entry, index) => (
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
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Package Registrations</h2>
              {adminStats.package_registration_chart.length === 0 ? (
                <p className="mt-5 text-sm font-medium text-slate-500">
                  No chart data available.
                </p>
              ) : (
                <div className="mt-5 h-72">
                  <ResponsiveContainer height="100%" width="100%">
                    <BarChart data={adminStats.package_registration_chart}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {role === "EMPLOYEE" && employeeStats ? (
        <section className="mt-6 grid gap-4 md:grid-cols-4">
          <StatCard
            label="Assigned customers"
            value={employeeStats.assigned_customers_count}
          />
          <StatCard
            label="Active subs"
            value={employeeStats.active_subscriptions_count}
          />
          <StatCard label="Pending follow-ups" value={employeeStats.pending_follow_ups} />
          <StatCard label="Open claims" value={employeeStats.open_claims_count} />
        </section>
      ) : null}

      {role === "CUSTOMER" && customerStats ? (
        <section className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <StatCard label="Active packages" value={customerStats.active_packages} />
            <StatCard label="Expired packages" value={customerStats.expired_packages} />
            <StatCard label="Open claims" value={customerStats.open_claims} />
            <StatCard
              label="Assigned employee"
              value={customerStats.assigned_employee?.full_name ?? "Unassigned"}
            />
          </div>

          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Latest Subscriptions</h2>
            {customerStats.latest_subscriptions.length === 0 ? (
              <p className="mt-5 text-sm font-medium text-slate-500">
                No subscriptions found.
              </p>
            ) : (
              <div className="mt-5 divide-y divide-slate-200">
                {customerStats.latest_subscriptions.map((subscription) => (
                  <div className="py-3" key={subscription.id}>
                    <p className="font-semibold">{subscription.package_name}</p>
                    <p className="mt-1 text-sm capitalize text-slate-500">
                      {subscription.policy_number} - {subscription.status}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      ) : null}
    </div>
  );
}
