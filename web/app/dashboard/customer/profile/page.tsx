"use client";

import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
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
        setError(err instanceof ApiError ? err.message : "Không thể tải hồ sơ cá nhân");
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadProfile();
    }
  }, [isReady, token]);

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  if (error || !profile) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {error ?? "Không tìm thấy hồ sơ khách hàng"}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Khách hàng</p>
        <h1 className="mt-2 text-3xl font-semibold">Hồ sơ của tôi</h1>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Tên</p>
          <p className="mt-2 font-semibold">{profile.full_name}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Mã khách hàng</p>
          <p className="mt-2 font-semibold">{profile.customer_code}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-slate-500">Trạng thái</p>
          <div className="mt-2"><StatusBadge value={profile.status} /></div>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Thông tin liên hệ</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
          <p>Email: {profile.email}</p>
          <p>Ngày sinh: {profile.date_of_birth || "Chưa cung cấp"}</p>
          <p>Số CCCD/CMND: {profile.identity_number || "Chưa cung cấp"}</p>
          <p>Địa chỉ: {profile.address || "Chưa cung cấp"}</p>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Nhân viên phụ trách</h2>
        {employee ? (
          <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
            <p>Họ và tên: {employee.full_name}</p>
            <p>Email: {employee.email}</p>
            <p>Mã: {employee.employee_code}</p>
            <p>Phòng ban: {employee.department || "Chưa cung cấp"}</p>
          </div>
        ) : (
          <p className="mt-4 text-sm font-medium text-slate-500">
            Chưa có nhân viên phụ trách.
          </p>
        )}
      </section>
    </div>
  );
}
