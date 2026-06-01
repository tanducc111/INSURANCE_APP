"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { clearStoredAuth } from "@/lib/auth-storage";

export function LogoutButton() {
  const router = useRouter();

  function handleLogout() {
    clearStoredAuth();
    router.replace("/login");
  }

  return (
    <button
      className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700"
      onClick={handleLogout}
      type="button"
    >
      <LogOut aria-hidden className="h-4 w-4" />
      Đăng xuất
    </button>
  );
}
