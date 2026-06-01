"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Menu, ShieldCheck } from "lucide-react";

import { LogoutButton } from "@/components/dashboard/logout-button";
import { RoleSidebar } from "@/components/dashboard/role-sidebar";
import { LoadingState } from "@/components/ui/loading-state";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  setStoredAuth,
} from "@/lib/auth-storage";
import { roleLabel } from "@/lib/formatters";
import { getMe } from "@/services/auth-service";
import type { AuthUser } from "@/types/auth";

export function ProtectedDashboardShell({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(getStoredUser);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    getMe(token)
      .then((freshUser) => {
        setStoredAuth(token, freshUser);
        setUser(freshUser);
      })
      .catch(() => {
        clearStoredAuth();
        router.replace("/login");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [router]);

  if (isLoading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-mist text-ink">
        <LoadingState label="Đang kiểm tra phiên đăng nhập..." />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-mist text-ink">
      <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
        <RoleSidebar user={user} />
        <section className="min-w-0 p-4 md:p-6 lg:p-8">
          <header className="mb-6 flex items-center justify-between rounded-lg border border-border bg-white px-4 py-3 shadow-sm lg:justify-end">
            <div className="flex items-center gap-3 lg:hidden">
              <button
                aria-label="Mở điều hướng"
                className="rounded-md border border-border p-2 text-muted"
                type="button"
              >
                <Menu aria-hidden className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2 font-extrabold">
                <ShieldCheck aria-hidden className="h-5 w-5 text-primary" />
                Bảo hiểm Việt
              </div>
            </div>
            <div className="hidden text-right md:block">
              <p className="text-sm font-bold text-ink">{user.full_name}</p>
              <p className="text-xs font-semibold text-muted">
                {roleLabel(user.role)}
              </p>
            </div>
            <LogoutButton />
          </header>
          {children}
        </section>
      </div>
    </main>
  );
}
