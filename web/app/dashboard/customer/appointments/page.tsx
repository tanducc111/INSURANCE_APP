"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppointmentStatusBadge } from "@/components/appointments/appointment-status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { listCustomerAppointments } from "@/services/communication-service";
import type { Appointment, AppointmentStatus } from "@/types/communication";

export default function CustomerAppointmentsPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
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
        await listCustomerAppointments(token, {
          status: statusFilter,
          limit: 100,
        }),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load appointments",
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
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-6xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-semibold">My Appointments</h1>
          <Link
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white"
            href="/dashboard/customer/book-appointment"
          >
            Book Appointment
          </Link>
        </div>
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
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
          <option value="rescheduled">Rescheduled</option>
          <option value="cancelled">Cancelled</option>
          <option value="completed">Completed</option>
        </select>
        <button
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
          type="submit"
        >
          Filter
        </button>
      </form>

      <section className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        {isLoading ? (
          <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
        ) : appointments.length === 0 ? (
          <p className="p-5 text-sm font-medium text-slate-500">
            No appointments found.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Schedule</th>
                  <th className="px-4 py-3">Employee</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Status</th>
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
                      {appointment.employee_name}
                    </td>
                    <td className="px-4 py-3">
                      {appointment.duration_minutes} minutes
                    </td>
                    <td className="px-4 py-3">
                      <AppointmentStatusBadge status={appointment.status} />
                    </td>
                    <td className="px-4 py-3">
                      {appointment.note || "No note"}
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
