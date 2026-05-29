"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  assignAdminClaim,
  listAdminClaims,
  updateAdminClaimStatus,
} from "@/services/claim-service";
import { listEmployees } from "@/services/customer-management-service";
import type {
  Claim,
  ClaimIncidentType,
  ClaimPriority,
  ClaimStatus,
} from "@/types/claim";
import type { Employee } from "@/types/customer-management";

export default function AdminClaimsPage() {
  const { isReady, token } = useAdminAccess();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<ClaimIncidentType | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<ClaimPriority | "all">(
    "all",
  );
  const [nextStatus, setNextStatus] = useState<ClaimStatus>("reviewing");
  const [assignedEmployeeValue, setAssignedEmployeeValue] = useState("none");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedClaim =
    claims.find((claim) => claim.id === selectedClaimId) ?? null;

  async function loadData() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [claimData, employeeData] = await Promise.all([
        listAdminClaims(token, {
          search,
          status: statusFilter,
          incidentType: typeFilter,
          priority: priorityFilter,
          limit: 100,
        }),
        listEmployees(token, { limit: 100 }),
      ]);
      setClaims(claimData);
      setEmployees(employeeData);
      setSelectedClaimId((current) =>
        claimData.some((claim) => claim.id === current)
          ? current
          : claimData[0]?.id ?? null,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load claims");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadData();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedClaim) {
      setNextStatus(selectedClaim.status);
      setAssignedEmployeeValue(
        selectedClaim.assigned_employee_id
          ? String(selectedClaim.assigned_employee_id)
          : "none",
      );
    }
  }, [selectedClaim?.id]);

  function replaceClaim(updatedClaim: Claim) {
    setClaims((current) =>
      current.map((claim) =>
        claim.id === updatedClaim.id ? updatedClaim : claim,
      ),
    );
    setSelectedClaimId(updatedClaim.id);
  }

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadData();
  }

  async function handleStatusSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(await updateAdminClaimStatus(token, selectedClaim.id, nextStatus));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to update status");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAssignmentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(
        await assignAdminClaim(
          token,
          selectedClaim.id,
          assignedEmployeeValue === "none" ? null : Number(assignedEmployeeValue),
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to assign claim");
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
        <p className="text-sm font-medium uppercase text-ocean">Admin</p>
        <h1 className="mt-2 text-3xl font-semibold">Claims</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form className="mt-6 flex flex-wrap gap-3" onSubmit={handleFilter}>
        <input
          className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search claims"
          value={search}
        />
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            setStatusFilter(event.target.value as ClaimStatus | "all")
          }
          value={statusFilter}
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="reviewing">Reviewing</option>
          <option value="need_more_documents">Need documents</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="completed">Completed</option>
        </select>
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            setTypeFilter(event.target.value as ClaimIncidentType | "all")
          }
          value={typeFilter}
        >
          <option value="all">All types</option>
          <option value="accident">Accident</option>
          <option value="hospital">Hospital</option>
          <option value="damage">Damage</option>
          <option value="other">Other</option>
        </select>
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            setPriorityFilter(event.target.value as ClaimPriority | "all")
          }
          value={priorityFilter}
        >
          <option value="all">All priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
        <button
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
          type="submit"
        >
          Filter
        </button>
      </form>

      <section className="mt-5 grid gap-6 xl:grid-cols-[1fr_420px]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
          ) : claims.length === 0 ? (
            <p className="p-5 text-sm font-medium text-slate-500">
              No claims found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[960px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Claim</th>
                    <th className="px-4 py-3">Customer</th>
                    <th className="px-4 py-3">Policy</th>
                    <th className="px-4 py-3">Employee</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {claims.map((claim) => (
                    <tr
                      className={`cursor-pointer ${
                        selectedClaimId === claim.id ? "bg-teal-50" : ""
                      }`}
                      key={claim.id}
                      onClick={() => setSelectedClaimId(claim.id)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold">{claim.title}</p>
                        <p className="text-xs capitalize text-slate-500">
                          {formatClaimLabel(claim.incident_type)}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold">{claim.customer_name}</p>
                        <p className="text-xs text-slate-500">
                          {claim.customer_code}
                        </p>
                      </td>
                      <td className="px-4 py-3">{claim.policy_number}</td>
                      <td className="px-4 py-3">
                        {claim.assigned_employee_name ?? "Unassigned"}
                      </td>
                      <td className="px-4 py-3 capitalize">{claim.priority}</td>
                      <td className="px-4 py-3">
                        <ClaimStatusBadge status={claim.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <aside className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          {selectedClaim ? (
            <div className="space-y-5">
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-semibold">{selectedClaim.title}</h2>
                  <ClaimStatusBadge status={selectedClaim.status} />
                </div>
                <p className="mt-2 text-sm text-slate-500">
                  {selectedClaim.customer_name} - {selectedClaim.package_name}
                </p>
              </div>

              <div className="grid gap-2 text-sm text-slate-600">
                <p>Policy: {selectedClaim.policy_number}</p>
                <p>Date: {selectedClaim.incident_date}</p>
                <p>Location: {selectedClaim.location || "Not provided"}</p>
                <p className="capitalize">
                  Type: {formatClaimLabel(selectedClaim.incident_type)}
                </p>
              </div>

              <p className="text-sm leading-6 text-slate-700">
                {selectedClaim.description}
              </p>

              <form className="grid gap-3" onSubmit={handleStatusSubmit}>
                <select
                  className="rounded-md border border-slate-300 px-3 py-2"
                  onChange={(event) =>
                    setNextStatus(event.target.value as ClaimStatus)
                  }
                  value={nextStatus}
                >
                  <option value="pending">Pending</option>
                  <option value="reviewing">Reviewing</option>
                  <option value="need_more_documents">Need documents</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="completed">Completed</option>
                </select>
                <button
                  className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                  disabled={isSaving}
                  type="submit"
                >
                  {isSaving ? "Saving..." : "Update Status"}
                </button>
              </form>

              <form className="grid gap-3" onSubmit={handleAssignmentSubmit}>
                <select
                  className="rounded-md border border-slate-300 px-3 py-2"
                  onChange={(event) => setAssignedEmployeeValue(event.target.value)}
                  value={assignedEmployeeValue}
                >
                  <option value="none">Unassigned</option>
                  {employees.map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.full_name} ({employee.employee_code})
                    </option>
                  ))}
                </select>
                <button
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:bg-slate-100"
                  disabled={isSaving}
                  type="submit"
                >
                  {isSaving ? "Saving..." : "Assign Employee"}
                </button>
              </form>

              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">
                  Review Note
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {selectedClaim.review_note || "No review note yet."}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">
                  Attachments
                </h3>
                {selectedClaim.attachments.length === 0 ? (
                  <p className="mt-3 text-sm font-medium text-slate-500">
                    No attachments uploaded.
                  </p>
                ) : (
                  <div className="mt-3 divide-y divide-slate-200">
                    {selectedClaim.attachments.map((attachment) => (
                      <a
                        className="block py-2 text-sm font-semibold text-ocean"
                        href={attachment.file_url}
                        key={attachment.id}
                      >
                        {attachment.file_name}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-500">
              Select a claim to manage.
            </p>
          )}
        </aside>
      </section>
    </div>
  );
}
