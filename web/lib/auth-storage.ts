import type { AuthUser } from "@/types/auth";

const TOKEN_KEY = "insurance_access_token";
const USER_KEY = "insurance_user";

function canUseStorage() {
  return typeof window !== "undefined";
}

export function getStoredToken(): string | null {
  if (!canUseStorage()) {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredAuth(token: string, user: AuthUser) {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): AuthUser | null {
  if (!canUseStorage()) {
    return null;
  }
  const rawUser = window.localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }
  try {
    return JSON.parse(rawUser) as AuthUser;
  } catch {
    return null;
  }
}

export function clearStoredAuth() {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}
