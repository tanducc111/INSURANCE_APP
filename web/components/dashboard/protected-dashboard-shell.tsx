"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LogoutButton } from "@/components/dashboard/logout-button";
import { RoleSidebar } from "@/components/dashboard/role-sidebar";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  setStoredAuth,
} from "@/lib/auth-storage";
import { getMe } from "@/services/auth-service";
import type { AuthUser } from "@/types/auth";

export function ProtectedDashboardShell({
  children,
}: Readonly<{
  children: React.ReactNode;
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
        <p className="text-sm font-medium text-slate-600">Loading...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-mist text-ink">
      <div className="grid min-h-screen md:grid-cols-[260px_1fr]">
        <RoleSidebar user={user} />
        <section className="p-6 md:p-8">
          <header className="mb-6 flex items-center justify-end">
            <LogoutButton />
          </header>
          {children}
        </section>
      </div>
    </main>
  );
}
