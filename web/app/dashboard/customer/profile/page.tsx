"use client";

import { useEffect, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  getCustomerAssignedEmployee,
  getCustomerProfile,
} from "@/services/customer-management-service";
import type { Customer, Employee } from "@/types/customer-management";

export default function CustomerProfilePage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [profile, setProfile] = useState<Customer | null>(null);
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const [profileData, employeeData] = await Promise.all([
          getCustomerProfile(token),
          getCustomerAssignedEmployee(token),
        ]);
        setProfile(profileData);
        setEmployee(employeeData);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load profile");
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadProfile();
    }
  }, [isReady, token]);

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  if (error || !profile) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {error ?? "Customer profile not found"}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">My Profile</h1>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Name</p>
          <p className="mt-2 font-semibold">{profile.full_name}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Code</p>
          <p className="mt-2 font-semibold">{profile.customer_code}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Status</p>
          <p className="mt-2 font-semibold capitalize">{profile.status}</p>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Contact Details</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
          <p>Email: {profile.email}</p>
          <p>Date of birth: {profile.date_of_birth || "Not provided"}</p>
          <p>Identity: {profile.identity_number || "Not provided"}</p>
          <p>Address: {profile.address || "Not provided"}</p>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Assigned Employee</h2>
        {employee ? (
          <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
            <p>Name: {employee.full_name}</p>
            <p>Email: {employee.email}</p>
            <p>Code: {employee.employee_code}</p>
            <p>Department: {employee.department || "Not provided"}</p>
          </div>
        ) : (
          <p className="mt-4 text-sm font-medium text-slate-500">
            No employee assigned yet.
          </p>
        )}
      </section>
    </div>
  );
}
