"use client";

import { FormEvent, useEffect, useState } from "react";

import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  createAssignment,
  listAssignments,
  listCustomers,
  listEmployees,
  updateAssignmentStatus,
} from "@/services/customer-management-service";
import type {
  AssignmentStatus,
  Customer,
  CustomerAssignment,
  Employee,
} from "@/types/customer-management";

export default function AdminAssignmentsPage() {
  const { isReady, token } = useAdminAccess();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [assignments, setAssignments] = useState<CustomerAssignment[]>([]);
  const [employeeId, setEmployeeId] = useState(0);
  const [customerId, setCustomerId] = useState(0);
  const [status, setStatus] = useState<AssignmentStatus>("active");
  const [statusFilter, setStatusFilter] = useState<AssignmentStatus | "all">("all");
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
      const [employeeData, customerData, assignmentData] = await Promise.all([
        listEmployees(token, { limit: 100 }),
        listCustomers(token, { limit: 100 }),
        listAssignments(token, { status: statusFilter, limit: 100 }),
      ]);
      setEmployees(employeeData);
      setCustomers(customerData);
      setAssignments(assignmentData);
      setEmployeeId((current) => current || employeeData[0]?.id || 0);
      setCustomerId((current) => current || customerData[0]?.id || 0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load assignments");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadData();
    }
  }, [isReady, token]);

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadData();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !customerId || !employeeId) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await createAssignment(token, {
        customer_id: customerId,
        employee_id: employeeId,
        status,
      });
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to assign customer");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleStatusChange(
    assignmentId: number,
    nextStatus: AssignmentStatus,
  ) {
    if (!token) {
      return;
    }
    setError(null);
    try {
      await updateAssignmentStatus(token, assignmentId, nextStatus);
      await loadData();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to update assignment",
      );
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Admin</p>
        <h1 className="mt-2 text-3xl font-semibold">Assignments</h1>
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
          <h2 className="text-lg font-semibold">Assign Customer</h2>
          <div className="mt-5 grid gap-4">
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              disabled={customers.length === 0}
              onChange={(event) => setCustomerId(Number(event.target.value))}
              value={customerId}
            >
              {customers.length === 0 ? (
                <option value={0}>No customers</option>
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
              disabled={employees.length === 0}
              onChange={(event) => setEmployeeId(Number(event.target.value))}
              value={employeeId}
            >
              {employees.length === 0 ? (
                <option value={0}>No employees</option>
              ) : (
                employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.full_name} ({employee.employee_code})
                  </option>
                ))
              )}
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setStatus(event.target.value as AssignmentStatus)}
              value={status}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <button
              className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={isSaving || !customerId || !employeeId}
              type="submit"
            >
              {isSaving ? "Saving..." : "Assign"}
            </button>
          </div>
        </form>

        <section>
          <form className="flex gap-3" onSubmit={handleFilter}>
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setStatusFilter(event.target.value as AssignmentStatus | "all")
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
              Filter
            </button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
            ) : assignments.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                No assignments found.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Customer</th>
                      <th className="px-4 py-3">Employee</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Assigned</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {assignments.map((assignment) => (
                      <tr key={assignment.id}>
                        <td className="px-4 py-3">
                          <p className="font-semibold">
                            {assignment.customer_name}
                          </p>
                          <p className="text-xs text-slate-500">
                            {assignment.customer_code}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-semibold">
                            {assignment.employee_name}
                          </p>
                          <p className="text-xs text-slate-500">
                            {assignment.employee_code}
                          </p>
                        </td>
                        <td className="px-4 py-3 capitalize">
                          {assignment.status}
                        </td>
                        <td className="px-4 py-3">
                          {new Date(assignment.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                            onClick={() =>
                              void handleStatusChange(
                                assignment.id,
                                assignment.status === "active"
                                  ? "inactive"
                                  : "active",
                              )
                            }
                            type="button"
                          >
                            {assignment.status === "active"
                              ? "Deactivate"
                              : "Activate"}
                          </button>
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
