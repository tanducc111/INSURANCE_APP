"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getStoredUser } from "@/lib/auth-storage";

export default function AdminUserManagementPage() {
  const router = useRouter();
  const user = getStoredUser();

  useEffect(() => {
    if (user && user.role !== "ADMIN") {
      router.replace("/dashboard");
    }
  }, [router, user]);

  if (user && user.role !== "ADMIN") {
    return null;
  }

  return (
    <div className="mx-auto max-w-6xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Quản lý người dùng</h1>
      </header>

      <div className="mt-6 rounded-md border border-dashed border-slate-300 bg-white p-6">
        <p className="text-sm font-medium text-slate-500">
          Công cụ quản lý người dùng sẽ được kết nối với API quản trị ở bước tiếp theo.
        </p>
      </div>
    </div>
  );
}
