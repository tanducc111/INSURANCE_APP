"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { createCustomerAppointment } from "@/services/communication-service";
import type { AppointmentPayload } from "@/types/communication";

const emptyForm: AppointmentPayload = {
  scheduled_at: "",
  duration_minutes: 30,
  note: "",
};

export default function CustomerBookAppointmentPage() {
  const router = useRouter();
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [form, setForm] = useState<AppointmentPayload>(emptyForm);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await createCustomerAppointment(token, {
        ...form,
        note: form.note?.trim() ? form.note : null,
      });
      router.push("/dashboard/customer/appointments");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to book appointment",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">Book Appointment</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form
        className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm"
        onSubmit={handleSubmit}
      >
        <div className="grid gap-4">
          <input
            className="rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) =>
              setForm({ ...form, scheduled_at: event.target.value })
            }
            required
            type="datetime-local"
            value={form.scheduled_at}
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
            required
            type="number"
            value={form.duration_minutes}
          />
          <textarea
            className="min-h-28 rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) => setForm({ ...form, note: event.target.value })}
            placeholder="Appointment note"
            value={form.note ?? ""}
          />
          <button
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={isSaving}
            type="submit"
          >
            {isSaving ? "Booking..." : "Book Appointment"}
          </button>
        </div>
      </form>
    </div>
  );
}
