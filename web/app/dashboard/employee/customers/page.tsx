"use client";

import { FormEvent, useEffect, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  createFollowUpNote,
  listAssignedCustomers,
  listFollowUpNotes,
} from "@/services/customer-management-service";
import { listEmployeeCustomerSubscriptions } from "@/services/subscription-service";
import type { Customer, FollowUpNote } from "@/types/customer-management";
import type { CustomerInsuranceSubscription } from "@/types/subscription";

export default function EmployeeCustomersPage() {
  const { isReady, token } = useRoleAccess(["EMPLOYEE"]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [notes, setNotes] = useState<FollowUpNote[]>([]);
  const [subscriptions, setSubscriptions] = useState<
    CustomerInsuranceSubscription[]
  >([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [nextActionAt, setNextActionAt] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isNotesLoading, setIsNotesLoading] = useState(false);
  const [isSubscriptionsLoading, setIsSubscriptionsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedCustomer =
    customers.find((customer) => customer.id === selectedCustomerId) ?? null;

  async function loadCustomers() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listAssignedCustomers(token, { limit: 100 });
      setCustomers(data);
      setSelectedCustomerId((current) => current || data[0]?.id || null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load customers");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadNotes(customerId: number) {
    if (!token) {
      return;
    }

    setIsNotesLoading(true);
    setError(null);
    try {
      const data = await listFollowUpNotes(token, customerId);
      setNotes(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load notes");
    } finally {
      setIsNotesLoading(false);
    }
  }

  async function loadSubscriptions(customerId: number) {
    if (!token) {
      return;
    }

    setIsSubscriptionsLoading(true);
    setError(null);
    try {
      const data = await listEmployeeCustomerSubscriptions(token, customerId, {
        limit: 100,
      });
      setSubscriptions(data);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load subscriptions",
      );
    } finally {
      setIsSubscriptionsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadCustomers();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedCustomerId) {
      void loadNotes(selectedCustomerId);
      void loadSubscriptions(selectedCustomerId);
    } else {
      setNotes([]);
      setSubscriptions([]);
    }
  }, [selectedCustomerId, token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedCustomerId) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await createFollowUpNote(token, selectedCustomerId, {
        note,
        next_action_at: nextActionAt || null,
      });
      setNote("");
      setNextActionAt("");
      await loadNotes(selectedCustomerId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save note");
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Employee</p>
        <h1 className="mt-2 text-3xl font-semibold">Assigned Customers</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
          ) : customers.length === 0 ? (
            <p className="p-5 text-sm font-medium text-slate-500">
              No assigned customers found.
            </p>
          ) : (
            <div className="divide-y divide-slate-200">
              {customers.map((customer) => (
                <button
                  className={`block w-full px-5 py-4 text-left transition ${
                    selectedCustomerId === customer.id
                      ? "bg-teal-50"
                      : "hover:bg-slate-50"
                  }`}
                  key={customer.id}
                  onClick={() => setSelectedCustomerId(customer.id)}
                  type="button"
                >
                  <p className="font-semibold">{customer.full_name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {customer.customer_code} - {customer.email}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        <section className="space-y-6">
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">
              {selectedCustomer ? selectedCustomer.full_name : "Customer"}
            </h2>
            {selectedCustomer ? (
              <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
                <p>Code: {selectedCustomer.customer_code}</p>
                <p>Email: {selectedCustomer.email}</p>
                <p>Status: {selectedCustomer.status}</p>
                <p>
                  Identity: {selectedCustomer.identity_number || "Not provided"}
                </p>
              </div>
            ) : (
              <p className="mt-4 text-sm font-medium text-slate-500">
                Select a customer to view details.
              </p>
            )}
          </div>

          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Subscriptions</h2>
            {isSubscriptionsLoading ? (
              <p className="mt-5 text-sm font-medium text-slate-500">
                Loading...
              </p>
            ) : subscriptions.length === 0 ? (
              <p className="mt-5 text-sm font-medium text-slate-500">
                No subscriptions found.
              </p>
            ) : (
              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Policy</th>
                      <th className="px-4 py-3">Package</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Payment</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {subscriptions.map((subscription) => (
                      <tr key={subscription.id}>
                        <td className="px-4 py-3">
                          {subscription.policy_number}
                        </td>
                        <td className="px-4 py-3">
                          {subscription.package_name}
                        </td>
                        <td className="px-4 py-3 capitalize">
                          {subscription.status}
                        </td>
                        <td className="px-4 py-3 capitalize">
                          {subscription.payment_status}
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
            <h2 className="text-lg font-semibold">Follow-up Note</h2>
            <div className="mt-5 grid gap-4">
              <textarea
                className="min-h-28 rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) => setNote(event.target.value)}
                placeholder="Write a care note"
                required
                value={note}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) => setNextActionAt(event.target.value)}
                type="datetime-local"
                value={nextActionAt}
              />
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving || !selectedCustomerId}
                type="submit"
              >
                {isSaving ? "Saving..." : "Save Note"}
              </button>
            </div>
          </form>

          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Notes</h2>
            {isNotesLoading ? (
              <p className="mt-5 text-sm font-medium text-slate-500">Loading...</p>
            ) : notes.length === 0 ? (
              <p className="mt-5 text-sm font-medium text-slate-500">
                No follow-up notes found.
              </p>
            ) : (
              <div className="mt-5 space-y-3">
                {notes.map((item) => (
                  <div
                    className="rounded-md border border-slate-200 p-4"
                    key={item.id}
                  >
                    <p className="text-sm leading-6 text-slate-700">{item.note}</p>
                    <div className="mt-3 flex flex-wrap gap-3 text-xs font-medium text-slate-500">
                      <span>{item.employee_name}</span>
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                      {item.next_action_at ? (
                        <span>
                          Next: {new Date(item.next_action_at).toLocaleString()}
                        </span>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}
