import { apiFetch } from "@/services/api-client";
import type {
  Claim,
  ClaimIncidentType,
  ClaimPayload,
  ClaimPriority,
  ClaimStatus,
} from "@/types/claim";

type ClaimListParams = {
  skip?: number;
  limit?: number;
  search?: string;
  status?: ClaimStatus | "all";
  incidentType?: ClaimIncidentType | "all";
  priority?: ClaimPriority | "all";
};

function toQuery(params: ClaimListParams = {}) {
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
  if (params.incidentType && params.incidentType !== "all") {
    query.set("incident_type", params.incidentType);
  }
  if (params.priority && params.priority !== "all") {
    query.set("priority", params.priority);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function createCustomerClaim(token: string, payload: ClaimPayload) {
  return apiFetch<Claim>("/customer/claims", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function listCustomerClaims(token: string, params?: ClaimListParams) {
  return apiFetch<Claim[]>(`/customer/claims${toQuery(params)}`, { token });
}

export function getCustomerClaim(token: string, claimId: number) {
  return apiFetch<Claim>(`/customer/claims/${claimId}`, { token });
}

export function listEmployeeClaims(token: string, params?: ClaimListParams) {
  return apiFetch<Claim[]>(`/employee/claims${toQuery(params)}`, { token });
}

export function getEmployeeClaim(token: string, claimId: number) {
  return apiFetch<Claim>(`/employee/claims/${claimId}`, { token });
}

export function updateEmployeeClaimStatus(
  token: string,
  claimId: number,
  status: ClaimStatus,
) {
  return apiFetch<Claim>(`/employee/claims/${claimId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
    token,
  });
}

export function addEmployeeReviewNote(
  token: string,
  claimId: number,
  reviewNote: string,
) {
  return apiFetch<Claim>(`/employee/claims/${claimId}/review-note`, {
    method: "PATCH",
    body: JSON.stringify({ review_note: reviewNote }),
    token,
  });
}

export function listAdminClaims(token: string, params?: ClaimListParams) {
  return apiFetch<Claim[]>(`/admin/claims${toQuery(params)}`, { token });
}

export function getAdminClaim(token: string, claimId: number) {
  return apiFetch<Claim>(`/admin/claims/${claimId}`, { token });
}

export function assignAdminClaim(
  token: string,
  claimId: number,
  assignedEmployeeId: number | null,
) {
  return apiFetch<Claim>(`/admin/claims/${claimId}/assignment`, {
    method: "PATCH",
    body: JSON.stringify({ assigned_employee_id: assignedEmployeeId }),
    token,
  });
}

export function updateAdminClaimStatus(
  token: string,
  claimId: number,
  status: ClaimStatus,
) {
  return apiFetch<Claim>(`/admin/claims/${claimId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
    token,
  });
}
