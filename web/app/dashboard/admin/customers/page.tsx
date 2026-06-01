"use client";

import { FormEvent, useEffect, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  createCustomer,
  listCustomers,
  updateCustomer,
} from "@/services/customer-management-service";
import type { UserStatus } from "@/types/auth";
import type { Customer, CustomerPayload } from "@/types/customer-management";

const emptyForm: CustomerPayload = {
  email: "",
  password: "ChangeMe123!",
  full_name: "",
  status: "active",
  customer_code: "",
  date_of_birth: "",
  address: "",
  identity_number: "",
};

export default function AdminCustomersPage() {
  const { isReady, token } = useAdminAccess();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [form, setForm] = useState<CustomerPayload>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCustomers() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listCustomers(token, { search, limit: 100 });
      setCustomers(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải khách hàng");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadCustomers();
    }
  }, [isReady, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadCustomers();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        date_of_birth: form.date_of_birth || null,
        address: form.address?.trim() ? form.address : null,
        identity_number: form.identity_number?.trim()
          ? form.identity_number
          : null,
      };
      if (editingId) {
        await updateCustomer(token, editingId, {
          full_name: payload.full_name,
          status: payload.status,
          customer_code: payload.customer_code,
          date_of_birth: payload.date_of_birth,
          address: payload.address,
          identity_number: payload.identity_number,
        });
      } else {
        await createCustomer(token, payload);
      }
      setForm(emptyForm);
      setEditingId(null);
      await loadCustomers();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể lưu khách hàng");
    } finally {
      setIsSaving(false);
    }
  }

  function handleEdit(customer: Customer) {
    setEditingId(customer.id);
    setForm({
      email: customer.email,
      password: "",
      full_name: customer.full_name,
      status: customer.status,
      customer_code: customer.customer_code,
      date_of_birth: customer.date_of_birth ?? "",
      address: customer.address ?? "",
      identity_number: customer.identity_number ?? "",
    });
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Khách hàng</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 xl:grid-cols-[380px_1fr]">
        <form
          className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={handleSubmit}
        >
          <h2 className="text-lg font-semibold">
            {editingId ? "Chỉnh sửa khách hàng" : "Tạo khách hàng"}
          </h2>
          <div className="mt-5 grid gap-4">
            <input
              className="rounded-md border border-slate-300 px-3 py-2 disabled:bg-slate-100"
              disabled={Boolean(editingId)}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="Email"
              required
              type="email"
              value={form.email}
            />
            {!editingId ? (
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, password: event.target.value })
                }
                placeholder="Mật khẩu ban đầu"
                required
                type="password"
                value={form.password ?? ""}
              />
            ) : null}
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, full_name: event.target.value })
              }
              placeholder="Họ và tên"
              required
              value={form.full_name}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, customer_code: event.target.value })
              }
              placeholder="Mã khách hàng"
              required
              value={form.customer_code}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, date_of_birth: event.target.value })
                }
                type="date"
                value={form.date_of_birth ?? ""}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, identity_number: event.target.value })
                }
                placeholder="Số CCCD/CMND"
                value={form.identity_number ?? ""}
              />
            </div>
            <textarea
              className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, address: event.target.value })
              }
              placeholder="Địa chỉ"
              value={form.address ?? ""}
            />
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, status: event.target.value as UserStatus })
              }
              value={form.status}
            >
              <option value="active">Đang hoạt động</option>
              <option value="inactive">Ngừng hoạt động</option>
            </select>
            <div className="flex gap-3">
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving}
                type="submit"
              >
                {isSaving ? "Đang lưu..." : "Lưu"}
              </button>
              {editingId ? (
                <button
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                  onClick={() => {
                    setEditingId(null);
                    setForm(emptyForm);
                  }}
                  type="button"
                >Hủy</button>
              ) : null}
            </div>
          </div>
        </form>

        <section>
          <form className="flex gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm khách hàng"
              value={search}
            />
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >Tìm kiếm</button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
            ) : customers.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                Chưa có khách hàng.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Khách hàng</th>
                      <th className="px-4 py-3">Số CCCD/CMND</th>
                      <th className="px-4 py-3">Trạng thái</th>
                      <th className="px-4 py-3">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {customers.map((customer) => (
                      <tr key={customer.id}>
                        <td className="px-4 py-3">
                          <p className="font-semibold">{customer.full_name}</p>
                          <p className="text-xs text-slate-500">
                            {customer.customer_code} - {customer.email}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          {customer.identity_number || "Chưa cung cấp"}
                        </td>
                        <td className="px-4 py-3"><StatusBadge value={customer.status} /></td>
                        <td className="px-4 py-3">
                          <button
                            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                            onClick={() => handleEdit(customer)}
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
