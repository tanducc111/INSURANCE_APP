import { apiFetch } from "@/services/api-client";
import type {
  AssignmentStatus,
  Customer,
  CustomerAssignment,
  CustomerAssignmentPayload,
  CustomerPayload,
  Employee,
  EmployeePayload,
  FollowUpNote,
  FollowUpNotePayload,
} from "@/types/customer-management";

type ListParams = {
  skip?: number;
  limit?: number;
  search?: string;
  status?: AssignmentStatus | "all";
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
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function listEmployees(token: string, params?: ListParams) {
  return apiFetch<Employee[]>(`/admin/employees${toQuery(params)}`, { token });
}

export function createEmployee(token: string, payload: EmployeePayload) {
  return apiFetch<Employee>("/admin/employees", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateEmployee(
  token: string,
  employeeId: number,
  payload: Partial<EmployeePayload>,
) {
  return apiFetch<Employee>(`/admin/employees/${employeeId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function listCustomers(token: string, params?: ListParams) {
  return apiFetch<Customer[]>(`/admin/customers${toQuery(params)}`, { token });
}

export function createCustomer(token: string, payload: CustomerPayload) {
  return apiFetch<Customer>("/admin/customers", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateCustomer(
  token: string,
  customerId: number,
  payload: Partial<CustomerPayload>,
) {
  return apiFetch<Customer>(`/admin/customers/${customerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function listAssignments(token: string, params?: ListParams) {
  return apiFetch<CustomerAssignment[]>(`/admin/assignments${toQuery(params)}`, {
    token,
  });
}

export function createAssignment(
  token: string,
  payload: CustomerAssignmentPayload,
) {
  return apiFetch<CustomerAssignment>("/admin/assignments", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateAssignmentStatus(
  token: string,
  assignmentId: number,
  status: AssignmentStatus,
) {
  return apiFetch<CustomerAssignment>(
    `/admin/assignments/${assignmentId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({ status }),
      token,
    },
  );
}

export function listAssignedCustomers(token: string, params?: ListParams) {
  return apiFetch<Customer[]>(`/employee/customers${toQuery(params)}`, { token });
}

export function listFollowUpNotes(token: string, customerId: number) {
  return apiFetch<FollowUpNote[]>(
    `/employee/customers/${customerId}/follow-up-notes`,
    { token },
  );
}

export function createFollowUpNote(
  token: string,
  customerId: number,
  payload: FollowUpNotePayload,
) {
  return apiFetch<FollowUpNote>(
    `/employee/customers/${customerId}/follow-up-notes`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    },
  );
}

export function getCustomerProfile(token: string) {
  return apiFetch<Customer>("/customer/profile", { token });
}

export function getCustomerAssignedEmployee(token: string) {
  return apiFetch<Employee | null>("/customer/assigned-employee", { token });
}
