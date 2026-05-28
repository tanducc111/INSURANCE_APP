import { apiFetch } from "@/services/api-client";
import type { AuthUser, LoginResponse } from "@/types/auth";

export async function login(email: string, password: string) {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(token: string) {
  return apiFetch<AuthUser>("/auth/me", {
    method: "GET",
    token,
  });
}
