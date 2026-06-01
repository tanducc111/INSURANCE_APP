import { getRoleLabel } from "@/lib/vi-labels";

export function formatCurrency(value: number | string | null | undefined) {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat("vi-VN", {
    currency: "VND",
    maximumFractionDigits: 0,
    style: "currency",
  }).format(Number.isFinite(amount) ? amount : 0);
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Chưa cập nhật";
  }
  return new Intl.DateTimeFormat("vi-VN").format(new Date(value));
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Chưa cập nhật";
  }
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function roleLabel(role: string) {
  return getRoleLabel(role);
}
