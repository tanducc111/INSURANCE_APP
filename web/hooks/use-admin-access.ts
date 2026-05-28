"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getStoredToken, getStoredUser } from "@/lib/auth-storage";

export function useAdminAccess() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUser = getStoredUser();

    if (!storedToken) {
      router.replace("/login");
      return;
    }

    if (storedUser?.role !== "ADMIN") {
      router.replace("/dashboard");
      return;
    }

    setToken(storedToken);
    setIsReady(true);
  }, [router]);

  return { isReady, token };
}
