"use client";

import { FormEvent, useEffect, useState } from "react";

import { AppointmentStatusBadge } from "@/components/appointments/appointment-status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  listEmployeeAppointments,
  updateEmployeeAppointment,
} from "@/services/communication-service";
import type {
  Appointment,
  AppointmentStatus,
  AppointmentUpdatePayload,
} from "@/types/communication";

export default function EmployeeAppointmentsPage() {
  const { isReady, token } = useRoleAccess(["EMPLOYEE"]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedAppointmentId, setSelectedAppointmentId] = useState<number | null>(
    null,
  );
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "all">(
    "all",
  );
  const [form, setForm] = useState<AppointmentUpdatePayload>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedAppointment =
    appointments.find((appointment) => appointment.id === selectedAppointmentId) ??
    null;

  async function loadAppointments() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listEmployeeAppointments(token, {
        status: statusFilter,
        limit: 100,
      });
      setAppointments(data);
      setSelectedAppointmentId((current) =>
        data.some((appointment) => appointment.id === current)
          ? current
          : data[0]?.id ?? null,
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

  useEffect(() => {
    if (selectedAppointment) {
      setForm({
        scheduled_at: selectedAppointment.scheduled_at.slice(0, 16),
        duration_minutes: selectedAppointment.duration_minutes,
        status: selectedAppointment.status,
        note: selectedAppointment.note ?? "",
      });
    }
  }, [selectedAppointment?.id]);

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadAppointments();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedAppointment) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const updated = await updateEmployeeAppointment(
        token,
        selectedAppointment.id,
        {
          ...form,
          note: form.note?.trim() ? form.note : null,
        },
      );
      setAppointments((current) =>
        current.map((appointment) =>
          appointment.id === updated.id ? updated : appointment,
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể cập nhật lịch hẹn",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Nhân viên</p>
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

      <section className="mt-5 grid gap-6 xl:grid-cols-[1fr_380px]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
          ) : appointments.length === 0 ? (
            <p className="p-5 text-sm font-medium text-slate-500">
              Chưa có lịch hẹn.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Thời gian hẹn</th>
                    <th className="px-4 py-3">Khách hàng</th>
                    <th className="px-4 py-3">Thời hạn</th>
                    <th className="px-4 py-3">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {appointments.map((appointment) => (
                    <tr
                      className={`cursor-pointer ${
                        selectedAppointmentId === appointment.id
                          ? "bg-teal-50"
                          : ""
                      }`}
                      key={appointment.id}
                      onClick={() => setSelectedAppointmentId(appointment.id)}
                    >
                      <td className="px-4 py-3 font-semibold">
                        {new Date(appointment.scheduled_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold">
                          {appointment.customer_name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {appointment.customer_code}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        {appointment.duration_minutes} phút
                      </td>
                      <td className="px-4 py-3">
                        <AppointmentStatusBadge status={appointment.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <form
          className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={handleSubmit}
        >
          <h2 className="text-lg font-semibold">Quản lý lịch hẹn</h2>
          {selectedAppointment ? (
            <div className="mt-5 grid gap-4">
              <p className="text-sm font-medium text-slate-500">
                {selectedAppointment.customer_name}
              </p>
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, scheduled_at: event.target.value })
                }
                type="datetime-local"
                value={form.scheduled_at ?? ""}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                max={480}
                min={15}
                onChange={(event) =>
                  setForm({
                    ...form,
                    duration_minutes: Number(event.target.value),
                  })
                }
                type="number"
                value={form.duration_minutes ?? 30}
              />
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({
                    ...form,
                    status: event.target.value as AppointmentStatus,
                  })
                }
                value={form.status ?? "pending"}
              >
                <option value="pending">Chờ xử lý</option>
                <option value="accepted">Đã chấp nhận</option>
                <option value="rejected">Từ chối</option>
                <option value="rescheduled">Đã đổi lịch</option>
                <option value="cancelled">Đã hủy</option>
                <option value="completed">Hoàn tất</option>
              </select>
              <textarea
                className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) => setForm({ ...form, note: event.target.value })}
                placeholder="Ghi chú"
                value={form.note ?? ""}
              />
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving}
                type="submit"
              >
                {isSaving ? "Đang lưu..." : "Lưu"}
              </button>
            </div>
          ) : (
            <p className="mt-5 text-sm font-medium text-slate-500">
              Chọn một lịch hẹn.
            </p>
          )}
        </form>
      </section>
    </div>
  );
}
