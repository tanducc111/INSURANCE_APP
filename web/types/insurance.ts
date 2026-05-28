import type { UserRole } from "@/types/auth";

export type InsuranceStatus = "active" | "inactive";

export type InsurancePackage = {
  id: number;
  code: string;
  name: string;
  package_type: string;
  description: string | null;
  premium_amount: string;
  coverage_amount: string;
  duration_months: number;
  status: InsuranceStatus;
  created_at: string;
  updated_at: string;
};

export type InsurancePackagePayload = {
  code: string;
  name: string;
  package_type: string;
  description?: string | null;
  premium_amount: string;
  coverage_amount: string;
  duration_months: number;
  status: InsuranceStatus;
};

export type InsuranceProcess = {
  id: number;
  package_id: number;
  name: string;
  description: string | null;
  status: InsuranceStatus;
  created_at: string;
  updated_at: string;
};

export type InsuranceProcessPayload = {
  package_id: number;
  name: string;
  description?: string | null;
  status: InsuranceStatus;
};

export type ProcessStep = {
  id: number;
  process_id: number;
  step_order: number;
  name: string;
  description: string | null;
  required_role: UserRole | null;
  created_at: string;
  updated_at: string;
};

export type ProcessStepPayload = {
  step_order: number;
  name: string;
  description?: string | null;
  required_role?: UserRole | null;
};
