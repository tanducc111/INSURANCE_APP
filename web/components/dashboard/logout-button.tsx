"use client";

import { useRouter } from "next/navigation";

import { clearStoredAuth } from "@/lib/auth-storage";

export function LogoutButton() {
  const router = useRouter();

  function handleLogout() {
    clearStoredAuth();
    router.replace("/login");
  }

  return (
    <button
      className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700"
      onClick={handleLogout}
      type="button"
    >
      Logout
    </button>
  );
}
