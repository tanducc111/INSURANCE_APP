"use client";

import { useEffect, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { listCustomerSubscriptions } from "@/services/subscription-service";
import type { CustomerInsuranceSubscription } from "@/types/subscription";

export default function CustomerSubscriptionsPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [subscriptions, setSubscriptions] = useState<CustomerInsuranceSubscription[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSubscriptions() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        setSubscriptions(await listCustomerSubscriptions(token, { limit: 100 }));
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

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-6xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">My Subscriptions</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        {subscriptions.length === 0 ? (
          <p className="p-5 text-sm font-medium text-slate-500">
            No subscriptions found.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Policy</th>
                  <th className="px-4 py-3">Package</th>
                  <th className="px-4 py-3">Dates</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Payment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {subscriptions.map((subscription) => (
                  <tr key={subscription.id}>
                    <td className="px-4 py-3 font-semibold">
                      {subscription.policy_number}
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-semibold">{subscription.package_name}</p>
                      <p className="text-xs text-slate-500">
                        {subscription.package_code}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      {subscription.start_date} to {subscription.end_date}
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
      </section>
    </div>
  );
}
