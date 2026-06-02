"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { clearStoredAuth } from "@/lib/auth-storage";

type LogoutButtonProps = {
  compact?: boolean;
};

export function LogoutButton({ compact = false }: LogoutButtonProps) {
  const router = useRouter();

  function handleLogout() {
    clearStoredAuth();
    router.replace("/login");
    router.refresh();
  }

  return (
    <button
      aria-label="Đăng xuất khỏi hệ thống"
      className={`inline-flex items-center justify-center gap-2 rounded-md border border-border bg-white text-sm font-bold text-muted transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
        compact ? "h-9 px-3" : "px-3.5 py-2"
      }`}
      onClick={handleLogout}
      title="Đăng xuất"
      type="button"
    >
      <LogOut aria-hidden className="h-4 w-4" />
      <span className={compact ? "hidden xl:inline" : "hidden sm:inline"}>
        Đăng xuất
      </span>
    </button>
  );
}
