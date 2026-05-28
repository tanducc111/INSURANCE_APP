"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  createPackage,
  deletePackage,
  listPackages,
  updatePackage,
} from "@/services/insurance-service";
import type {
  InsurancePackage,
  InsurancePackagePayload,
  InsuranceStatus,
} from "@/types/insurance";

const emptyForm: InsurancePackagePayload = {
  code: "",
  name: "",
  package_type: "",
  description: "",
  premium_amount: "0",
  coverage_amount: "0",
  duration_months: 12,
  status: "active",
};

export default function AdminInsurancePackagesPage() {
  const { isReady, token } = useAdminAccess();
  const [packages, setPackages] = useState<InsurancePackage[]>([]);
  const [form, setForm] = useState<InsurancePackagePayload>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<InsuranceStatus | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadPackages() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listPackages(token, {
        search,
        status: statusFilter,
        limit: 100,
      });
      setPackages(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load packages");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadPackages();
    }
  }, [isReady, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadPackages();
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
        description: form.description?.trim() ? form.description : null,
        duration_months: Number(form.duration_months),
      };

      if (editingId) {
        await updatePackage(token, editingId, payload);
      } else {
        await createPackage(token, payload);
      }
      setForm(emptyForm);
      setEditingId(null);
      await loadPackages();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save package");
    } finally {
      setIsSaving(false);
    }
  }

  function handleEdit(packageItem: InsurancePackage) {
    setEditingId(packageItem.id);
    setForm({
      code: packageItem.code,
      name: packageItem.name,
      package_type: packageItem.package_type,
      description: packageItem.description ?? "",
      premium_amount: String(packageItem.premium_amount),
      coverage_amount: String(packageItem.coverage_amount),
      duration_months: packageItem.duration_months,
      status: packageItem.status,
    });
  }

  async function handleDeactivate(packageId: number) {
    if (!token) {
      return;
    }
    await updatePackage(token, packageId, { status: "inactive" });
    await loadPackages();
  }

  async function handleDelete(packageId: number) {
    if (!token || !window.confirm("Delete this package?")) {
      return;
    }
    await deletePackage(token, packageId);
    await loadPackages();
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Admin</p>
        <h1 className="mt-2 text-3xl font-semibold">Insurance Packages</h1>
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
            {editingId ? "Edit Package" : "Create Package"}
          </h2>
          <div className="mt-5 grid gap-4">
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setForm({ ...form, code: event.target.value })}
              placeholder="Code"
              required
              value={form.code}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Name"
              required
              value={form.name}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, package_type: event.target.value })
              }
              placeholder="Type"
              required
              value={form.package_type}
            />
            <textarea
              className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, description: event.target.value })
              }
              placeholder="Description"
              value={form.description ?? ""}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                min="0"
                onChange={(event) =>
                  setForm({ ...form, premium_amount: event.target.value })
                }
                placeholder="Premium"
                required
                step="0.01"
                type="number"
                value={form.premium_amount}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                min="0"
                onChange={(event) =>
                  setForm({ ...form, coverage_amount: event.target.value })
                }
                placeholder="Coverage"
                required
                step="0.01"
                type="number"
                value={form.coverage_amount}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                min="1"
                onChange={(event) =>
                  setForm({
                    ...form,
                    duration_months: Number(event.target.value),
                  })
                }
                placeholder="Duration"
                required
                type="number"
                value={form.duration_months}
              />
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({
                    ...form,
                    status: event.target.value as InsuranceStatus,
                  })
                }
                value={form.status}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving}
                type="submit"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
              {editingId ? (
                <button
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                  onClick={() => {
                    setEditingId(null);
                    setForm(emptyForm);
                  }}
                  type="button"
                >
                  Cancel
                </button>
              ) : null}
            </div>
          </div>
        </form>

        <section>
          <form className="flex flex-wrap gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search packages"
              value={search}
            />
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setStatusFilter(event.target.value as InsuranceStatus | "all")
              }
              value={statusFilter}
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >
              Search
            </button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
            ) : packages.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                No packages found.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Package</th>
                      <th className="px-4 py-3">Premium</th>
                      <th className="px-4 py-3">Coverage</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {packages.map((packageItem) => (
                      <tr key={packageItem.id}>
                        <td className="px-4 py-3">
                          <Link
                            className="font-semibold text-ocean hover:text-teal-800"
                            href={`/dashboard/admin/insurance/packages/${packageItem.id}`}
                          >
                            {packageItem.name}
                          </Link>
                          <p className="text-xs text-slate-500">
                            {packageItem.code} - {packageItem.package_type}
                          </p>
                        </td>
                        <td className="px-4 py-3">{packageItem.premium_amount}</td>
                        <td className="px-4 py-3">{packageItem.coverage_amount}</td>
                        <td className="px-4 py-3 capitalize">
                          {packageItem.status}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            <button
                              className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                              onClick={() => handleEdit(packageItem)}
                              type="button"
                            >
                              Edit
                            </button>
                            <button
                              className="rounded-md border border-amber-300 px-3 py-1 text-xs font-semibold text-amber-700"
                              onClick={() => void handleDeactivate(packageItem.id)}
                              type="button"
                            >
                              Deactivate
                            </button>
                            <button
                              className="rounded-md border border-red-300 px-3 py-1 text-xs font-semibold text-red-700"
                              onClick={() => void handleDelete(packageItem.id)}
                              type="button"
                            >
                              Delete
                            </button>
                          </div>
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
