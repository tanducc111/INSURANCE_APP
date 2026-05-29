import type { Employee } from "@/types/customer-management";

export type SubscriptionStatus = "pending" | "active" | "expired" | "cancelled";

export type PaymentStatus = "unpaid" | "paid" | "overdue";

export type CustomerInsuranceSubscription = {
  id: number;
  customer_id: number;
  package_id: number;
  start_date: string;
  end_date: string;
  status: SubscriptionStatus;
  payment_status: PaymentStatus;
  policy_number: string;
  premium_amount: string;
  customer_name: string;
  customer_code: string;
  package_name: string;
  package_code: string;
  created_at: string;
  updated_at: string;
};

export type CustomerInsuranceSubscriptionPayload = {
  customer_id: number;
  package_id: number;
  start_date: string;
  end_date: string;
  status: SubscriptionStatus;
  payment_status: PaymentStatus;
  policy_number: string;
  premium_amount: string;
};

export type ChartDataPoint = {
  label: string;
  value: number;
};

export type AdminDashboardStats = {
  total_customers: number;
  total_employees: number;
  total_packages: number;
  active_subscriptions: number;
  pending_subscriptions: number;
  open_claims: number;
  approved_claims: number;
  subscription_status_chart: ChartDataPoint[];
  package_registration_chart: ChartDataPoint[];
};

export type EmployeeDashboardStats = {
  assigned_customers_count: number;
  active_subscriptions_count: number;
  pending_follow_ups: number;
  open_claims_count: number;
};

export type CustomerDashboardStats = {
  active_packages: number;
  expired_packages: number;
  open_claims: number;
  assigned_employee: Employee | null;
  latest_subscriptions: CustomerInsuranceSubscription[];
};
