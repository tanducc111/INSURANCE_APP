import { apiFetch } from "@/services/api-client";
import type {
  AdminDashboardStats,
  CustomerDashboardStats,
  CustomerInsuranceSubscription,
  CustomerInsuranceSubscriptionPayload,
  EmployeeDashboardStats,
  PaymentStatus,
  SubscriptionStatus,
} from "@/types/subscription";

type ListParams = {
  skip?: number;
  limit?: number;
  search?: string;
  status?: SubscriptionStatus | "all";
  paymentStatus?: PaymentStatus | "all";
};

function toQuery(params: ListParams = {}) {
  const query = new URLSearchParams();
  if (params.skip !== undefined) {
    query.set("skip", String(params.skip));
  }
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.search) {
    query.set("search", params.search);
  }
  if (params.status && params.status !== "all") {
    query.set("status", params.status);
  }
  if (params.paymentStatus && params.paymentStatus !== "all") {
    query.set("payment_status", params.paymentStatus);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function listAdminSubscriptions(token: string, params?: ListParams) {
  return apiFetch<CustomerInsuranceSubscription[]>(
    `/admin/subscriptions${toQuery(params)}`,
    { token },
  );
}

export function createSubscription(
  token: string,
  payload: CustomerInsuranceSubscriptionPayload,
) {
  return apiFetch<CustomerInsuranceSubscription>("/admin/subscriptions", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateSubscription(
  token: string,
  subscriptionId: number,
  payload: Partial<CustomerInsuranceSubscriptionPayload>,
) {
  return apiFetch<CustomerInsuranceSubscription>(
    `/admin/subscriptions/${subscriptionId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      token,
    },
  );
}

export function listCustomerSubscriptions(token: string, params?: ListParams) {
  return apiFetch<CustomerInsuranceSubscription[]>(
    `/customer/subscriptions${toQuery(params)}`,
    { token },
  );
}

export function listEmployeeCustomerSubscriptions(
  token: string,
  customerId: number,
  params?: ListParams,
) {
  return apiFetch<CustomerInsuranceSubscription[]>(
    `/employee/customers/${customerId}/subscriptions${toQuery(params)}`,
    { token },
  );
}

export function getAdminDashboard(token: string) {
  return apiFetch<AdminDashboardStats>("/dashboard/admin", { token });
}

export function getEmployeeDashboard(token: string) {
  return apiFetch<EmployeeDashboardStats>("/dashboard/employee", { token });
}

export function getCustomerDashboard(token: string) {
  return apiFetch<CustomerDashboardStats>("/dashboard/customer", { token });
}
