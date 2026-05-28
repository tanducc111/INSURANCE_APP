"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getStoredToken, getStoredUser } from "@/lib/auth-storage";
import type { UserRole } from "@/types/auth";

export function useRoleAccess(allowedRoles: UserRole[]) {
  const router = useRouter();
  const rolesKey = allowedRoles.join(",");
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUser = getStoredUser();

    if (!storedToken) {
      router.replace("/login");
      return;
    }

    if (!storedUser || !allowedRoles.includes(storedUser.role)) {
      router.replace("/dashboard");
      return;
    }

    setToken(storedToken);
    setIsReady(true);
  }, [rolesKey, router]);

  return { isReady, token };
}
