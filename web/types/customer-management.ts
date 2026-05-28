import type { UserStatus } from "@/types/auth";

export type AssignmentStatus = "active" | "inactive";

export type Employee = {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  status: UserStatus;
  employee_code: string;
  department: string | null;
  position: string | null;
  hire_date: string | null;
  created_at: string;
  updated_at: string;
};

export type EmployeePayload = {
  email: string;
  password?: string;
  full_name: string;
  status: UserStatus;
  employee_code: string;
  department?: string | null;
  position?: string | null;
  hire_date?: string | null;
};

export type Customer = {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  status: UserStatus;
  customer_code: string;
  date_of_birth: string | null;
  address: string | null;
  identity_number: string | null;
  created_at: string;
  updated_at: string;
};

export type CustomerPayload = {
  email: string;
  password?: string;
  full_name: string;
  status: UserStatus;
  customer_code: string;
  date_of_birth?: string | null;
  address?: string | null;
  identity_number?: string | null;
};

export type CustomerAssignment = {
  id: number;
  customer_id: number;
  employee_id: number;
  status: AssignmentStatus;
  customer_name: string;
  customer_code: string;
  employee_name: string;
  employee_code: string;
  created_at: string;
  updated_at: string;
};

export type CustomerAssignmentPayload = {
  customer_id: number;
  employee_id: number;
  status: AssignmentStatus;
};

export type FollowUpNote = {
  id: number;
  customer_id: number;
  employee_id: number;
  note: string;
  next_action_at: string | null;
  employee_name: string;
  customer_name: string;
  created_at: string;
  updated_at: string;
};

export type FollowUpNotePayload = {
  note: string;
  next_action_at?: string | null;
};
