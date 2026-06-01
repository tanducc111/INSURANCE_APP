"use client";

import { FormEvent, useEffect, useState } from "react";

import { AppointmentStatusBadge } from "@/components/appointments/appointment-status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import { listAdminAppointments } from "@/services/communication-service";
import type { Appointment, AppointmentStatus } from "@/types/communication";

export default function AdminAppointmentsPage() {
  const { isReady, token } = useAdminAccess();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "all">(
    "all",
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAppointments() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setAppointments(
        await listAdminAppointments(token, {
          status: statusFilter,
          limit: 100,
        }),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể tải lịch hẹn",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadAppointments();
    }
  }, [isReady, token]);

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadAppointments();
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Lịch hẹn</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form className="mt-6 flex gap-3" onSubmit={handleFilter}>
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            setStatusFilter(event.target.value as AppointmentStatus | "all")
          }
          value={statusFilter}
        >
          <option value="all">Tất cả trạng thái</option>
          <option value="pending">Chờ xử lý</option>
          <option value="accepted">Đã chấp nhận</option>
          <option value="rejected">Từ chối</option>
          <option value="rescheduled">Đã đổi lịch</option>
          <option value="cancelled">Đã hủy</option>
          <option value="completed">Hoàn tất</option>
        </select>
        <button
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
          type="submit"
        >
          Lọc
        </button>
      </form>

      <section className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        {isLoading ? (
          <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
        ) : appointments.length === 0 ? (
          <p className="p-5 text-sm font-medium text-slate-500">
            Chưa có lịch hẹn.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                    <th className="px-4 py-3">Thời gian hẹn</th>
                  <th className="px-4 py-3">Khách hàng</th>
                  <th className="px-4 py-3">Nhân viên</th>
                  <th className="px-4 py-3">Thời hạn</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td className="px-4 py-3 font-semibold">
                      {new Date(appointment.scheduled_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-semibold">{appointment.customer_name}</p>
                      <p className="text-xs text-slate-500">
                        {appointment.customer_code}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-semibold">{appointment.employee_name}</p>
                      <p className="text-xs text-slate-500">
                        {appointment.employee_code}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                        {appointment.duration_minutes} phút
                    </td>
                    <td className="px-4 py-3">
                      <AppointmentStatusBadge status={appointment.status} />
                    </td>
                    <td className="px-4 py-3">
                      {appointment.note || "Chưa có ghi chú"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
