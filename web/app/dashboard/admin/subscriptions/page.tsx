"use client";

import { FormEvent, useEffect, useState } from "react";

import { useAdminAccess } from "@/hooks/use-admin-access";
import {
  getPaymentStatusLabel,
  getSubscriptionStatusLabel,
} from "@/lib/vi-labels";
import { ApiError } from "@/services/api-client";
import {
  listCustomers,
} from "@/services/customer-management-service";
import { listPackages } from "@/services/insurance-service";
import {
  createSubscription,
  listAdminSubscriptions,
  updateSubscription,
} from "@/services/subscription-service";
import type { Customer } from "@/types/customer-management";
import type { InsurancePackage } from "@/types/insurance";
import type {
  CustomerInsuranceSubscription,
  CustomerInsuranceSubscriptionPayload,
  PaymentStatus,
  SubscriptionStatus,
} from "@/types/subscription";

const emptyForm: CustomerInsuranceSubscriptionPayload = {
  customer_id: 0,
  package_id: 0,
  start_date: "",
  end_date: "",
  status: "pending",
  payment_status: "unpaid",
  policy_number: "",
  premium_amount: "0",
};

export default function AdminSubscriptionsPage() {
  const { isReady, token } = useAdminAccess();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [packages, setPackages] = useState<InsurancePackage[]>([]);
  const [subscriptions, setSubscriptions] = useState<CustomerInsuranceSubscription[]>(
    [],
  );
  const [form, setForm] =
    useState<CustomerInsuranceSubscriptionPayload>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<SubscriptionStatus | "all">(
    "all",
  );
  const [paymentFilter, setPaymentFilter] = useState<PaymentStatus | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [customerData, packageData, subscriptionData] = await Promise.all([
        listCustomers(token, { limit: 100 }),
        listPackages(token, { limit: 100 }),
        listAdminSubscriptions(token, {
          search,
          status: statusFilter,
          paymentStatus: paymentFilter,
          limit: 100,
        }),
      ]);
      setCustomers(customerData);
      setPackages(packageData);
      setSubscriptions(subscriptionData);
      setForm((current) => ({
        ...current,
        customer_id: current.customer_id || customerData[0]?.id || 0,
        package_id: current.package_id || packageData[0]?.id || 0,
      }));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể tải hợp đồng bảo hiểm",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadData();
    }
  }, [isReady, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadData();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !form.customer_id || !form.package_id) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        premium_amount: String(form.premium_amount),
      };
      if (editingId) {
        await updateSubscription(token, editingId, payload);
      } else {
        await createSubscription(token, payload);
      }
      setEditingId(null);
      setForm({
        ...emptyForm,
        customer_id: customers[0]?.id || 0,
        package_id: packages[0]?.id || 0,
      });
      await loadData();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể lưu hợp đồng bảo hiểm",
      );
    } finally {
      setIsSaving(false);
    }
  }

  function handleEdit(subscription: CustomerInsuranceSubscription) {
    setEditingId(subscription.id);
    setForm({
      customer_id: subscription.customer_id,
      package_id: subscription.package_id,
      start_date: subscription.start_date,
      end_date: subscription.end_date,
      status: subscription.status,
      payment_status: subscription.payment_status,
      policy_number: subscription.policy_number,
      premium_amount: String(subscription.premium_amount),
    });
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Hợp đồng bảo hiểm</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 xl:grid-cols-[400px_1fr]">
        <form
          className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={handleSubmit}
        >
          <h2 className="text-lg font-semibold">
            {editingId ? "Chỉnh sửa hợp đồng bảo hiểm" : "Tạo hợp đồng bảo hiểm"}
          </h2>
          <div className="mt-5 grid gap-4">
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              disabled={customers.length === 0}
              onChange={(event) =>
                setForm({ ...form, customer_id: Number(event.target.value) })
              }
              value={form.customer_id}
            >
              {customers.length === 0 ? (
                <option value={0}>Chưa có khách hàng</option>
              ) : (
                customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.full_name} ({customer.customer_code})
                  </option>
                ))
              )}
            </select>

            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              disabled={packages.length === 0}
              onChange={(event) =>
                setForm({ ...form, package_id: Number(event.target.value) })
              }
              value={form.package_id}
            >
              {packages.length === 0 ? (
                <option value={0}>Chưa có gói bảo hiểm</option>
              ) : (
                packages.map((packageItem) => (
                  <option key={packageItem.id} value={packageItem.id}>
                    {packageItem.name} ({packageItem.code})
                  </option>
                ))
              )}
            </select>

            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, policy_number: event.target.value })
              }
              placeholder="Số hợp đồng bảo hiểm"
              required
              value={form.policy_number}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, start_date: event.target.value })
                }
                required
                type="date"
                value={form.start_date}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, end_date: event.target.value })
                }
                required
                type="date"
                value={form.end_date}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({
                    ...form,
                    status: event.target.value as SubscriptionStatus,
                  })
                }
                value={form.status}
              >
                <option value="pending">Chờ kích hoạt</option>
                <option value="active">Đang hiệu lực</option>
                <option value="expired">Hết hạn</option>
                <option value="cancelled">Đã hủy</option>
              </select>
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({
                    ...form,
                    payment_status: event.target.value as PaymentStatus,
                  })
                }
                value={form.payment_status}
              >
                <option value="unpaid">Chưa thanh toán</option>
                <option value="paid">Đã thanh toán</option>
                <option value="overdue">Quá hạn</option>
              </select>
            </div>

            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              min="0"
              onChange={(event) =>
                setForm({ ...form, premium_amount: event.target.value })
              }
              placeholder="Số tiền phí bảo hiểm"
              required
              step="0.01"
              type="number"
              value={form.premium_amount}
            />

            <div className="flex gap-3">
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving || customers.length === 0 || packages.length === 0}
                type="submit"
              >
                {isSaving ? "Đang lưu..." : "Lưu"}
              </button>
              {editingId ? (
                <button
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                  onClick={() => {
                    setEditingId(null);
                    setForm({
                      ...emptyForm,
                      customer_id: customers[0]?.id || 0,
                      package_id: packages[0]?.id || 0,
                    });
                  }}
                  type="button"
                >Hủy</button>
              ) : null}
            </div>
          </div>
        </form>

        <section>
          <form className="flex flex-wrap gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm hợp đồng, khách hàng, gói bảo hiểm"
              value={search}
            />
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setStatusFilter(event.target.value as SubscriptionStatus | "all")
              }
              value={statusFilter}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="pending">Chờ kích hoạt</option>
              <option value="active">Đang hiệu lực</option>
              <option value="expired">Hết hạn</option>
              <option value="cancelled">Đã hủy</option>
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setPaymentFilter(event.target.value as PaymentStatus | "all")
              }
              value={paymentFilter}
            >
              <option value="all">Tất cả thanh toán</option>
              <option value="unpaid">Chưa thanh toán</option>
              <option value="paid">Đã thanh toán</option>
              <option value="overdue">Quá hạn</option>
            </select>
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >Tìm kiếm</button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
            ) : subscriptions.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                Chưa có hợp đồng bảo hiểm.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Hợp đồng</th>
                      <th className="px-4 py-3">Khách hàng</th>
                      <th className="px-4 py-3">Gói bảo hiểm</th>
                      <th className="px-4 py-3">Trạng thái</th>
                      <th className="px-4 py-3">Thanh toán</th>
                      <th className="px-4 py-3">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {subscriptions.map((subscription) => (
                      <tr key={subscription.id}>
                        <td className="px-4 py-3">
                          <p className="font-semibold">
                            {subscription.policy_number}
                          </p>
                          <p className="text-xs text-slate-500">
                            {subscription.start_date} đến {subscription.end_date}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          {subscription.customer_name}
                        </td>
                        <td className="px-4 py-3">
                          {subscription.package_name}
                        </td>
                        <td className="px-4 py-3 capitalize">
                          {getSubscriptionStatusLabel(subscription.status)}
                        </td>
                        <td className="px-4 py-3 capitalize">
                          {getPaymentStatusLabel(subscription.payment_status)}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                            onClick={() => handleEdit(subscription)}
                            type="button"
                          >Chỉnh sửa</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}
