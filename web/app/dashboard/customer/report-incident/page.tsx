"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { createCustomerClaim } from "@/services/claim-service";
import { listCustomerSubscriptions } from "@/services/subscription-service";
import type {
  ClaimIncidentType,
  ClaimPayload,
  ClaimPriority,
} from "@/types/claim";
import type { CustomerInsuranceSubscription } from "@/types/subscription";

const emptyForm: ClaimPayload = {
  subscription_id: 0,
  title: "",
  description: "",
  incident_type: "accident",
  incident_date: "",
  location: "",
  priority: "medium",
  attachments: [],
};

export default function CustomerReportIncidentPage() {
  const router = useRouter();
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [subscriptions, setSubscriptions] = useState<
    CustomerInsuranceSubscription[]
  >([]);
  const [form, setForm] = useState<ClaimPayload>(emptyForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSubscriptions() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await listCustomerSubscriptions(token, { limit: 100 });
        setSubscriptions(data);
        setForm((current) => ({
          ...current,
          subscription_id: current.subscription_id || data[0]?.id || 0,
        }));
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Unable to load subscriptions",
        );
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadSubscriptions();
    }
  }, [isReady, token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !form.subscription_id) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const claim = await createCustomerClaim(token, {
        ...form,
        location: form.location?.trim() ? form.location : null,
        attachments: [],
      });
      router.push(`/dashboard/customer/claims/${claim.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to submit claim");
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">Report Incident</h1>
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
          <select
            className="rounded-md border border-slate-300 px-3 py-2"
            disabled={subscriptions.length === 0}
            onChange={(event) =>
              setForm({ ...form, subscription_id: Number(event.target.value) })
            }
            required
            value={form.subscription_id}
          >
            {subscriptions.length === 0 ? (
              <option value={0}>No subscriptions</option>
            ) : (
              subscriptions.map((subscription) => (
                <option key={subscription.id} value={subscription.id}>
                  {subscription.policy_number} - {subscription.package_name}
                </option>
              ))
            )}
          </select>

          <input
            className="rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            placeholder="Claim title"
            required
            value={form.title}
          />

          <textarea
            className="min-h-32 rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
            placeholder="Incident description"
            required
            value={form.description}
          />

          <div className="grid gap-4 md:grid-cols-2">
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({
                  ...form,
                  incident_type: event.target.value as ClaimIncidentType,
                })
              }
              value={form.incident_type}
            >
              <option value="accident">Accident</option>
              <option value="hospital">Hospital</option>
              <option value="damage">Damage</option>
              <option value="other">Other</option>
            </select>

            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({
                  ...form,
                  priority: event.target.value as ClaimPriority,
                })
              }
              value={form.priority}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, incident_date: event.target.value })
              }
              required
              type="date"
              value={form.incident_date}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, location: event.target.value })
              }
              placeholder="Location"
              value={form.location ?? ""}
            />
          </div>

          <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-4">
            <input
              className="block w-full text-sm text-slate-500"
              disabled
              type="file"
            />
            <p className="mt-2 text-sm font-medium text-slate-500">
              Attachment upload placeholder.
            </p>
          </div>

          <button
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={isSaving || subscriptions.length === 0}
            type="submit"
          >
            {isSaving ? "Submitting..." : "Submit Claim"}
          </button>
        </div>
      </form>
    </div>
  );
}
