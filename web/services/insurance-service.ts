import { apiFetch } from "@/services/api-client";
import type {
  InsurancePackage,
  InsurancePackagePayload,
  InsuranceProcess,
  InsuranceProcessPayload,
  InsuranceStatus,
  ProcessStep,
  ProcessStepPayload,
} from "@/types/insurance";

type ListParams = {
  skip?: number;
  limit?: number;
  search?: string;
  status?: InsuranceStatus | "all";
  packageId?: number;
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
  if (params.packageId !== undefined) {
    query.set("package_id", String(params.packageId));
  }

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function listPackages(token: string, params?: ListParams) {
  return apiFetch<InsurancePackage[]>(`/insurance/packages${toQuery(params)}`, {
    token,
  });
}

export function getPackage(token: string, packageId: number) {
  return apiFetch<InsurancePackage>(`/insurance/packages/${packageId}`, {
    token,
  });
}

export function createPackage(token: string, payload: InsurancePackagePayload) {
  return apiFetch<InsurancePackage>("/insurance/packages", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updatePackage(
  token: string,
  packageId: number,
  payload: Partial<InsurancePackagePayload>,
) {
  return apiFetch<InsurancePackage>(`/insurance/packages/${packageId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function deletePackage(token: string, packageId: number) {
  return apiFetch<void>(`/insurance/packages/${packageId}`, {
    method: "DELETE",
    token,
  });
}

export function listProcesses(token: string, params?: ListParams) {
  return apiFetch<InsuranceProcess[]>(`/insurance/processes${toQuery(params)}`, {
    token,
  });
}

export function createProcess(token: string, payload: InsuranceProcessPayload) {
  return apiFetch<InsuranceProcess>("/insurance/processes", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateProcess(
  token: string,
  processId: number,
  payload: Partial<InsuranceProcessPayload>,
) {
  return apiFetch<InsuranceProcess>(`/insurance/processes/${processId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function deleteProcess(token: string, processId: number) {
  return apiFetch<void>(`/insurance/processes/${processId}`, {
    method: "DELETE",
    token,
  });
}

export function listSteps(token: string, processId: number, params?: ListParams) {
  return apiFetch<ProcessStep[]>(
    `/insurance/processes/${processId}/steps${toQuery(params)}`,
    { token },
  );
}

export function createStep(
  token: string,
  processId: number,
  payload: ProcessStepPayload,
) {
  return apiFetch<ProcessStep>(`/insurance/processes/${processId}/steps`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function updateStep(
  token: string,
  stepId: number,
  payload: Partial<ProcessStepPayload>,
) {
  return apiFetch<ProcessStep>(`/insurance/steps/${stepId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function deleteStep(token: string, stepId: number) {
  return apiFetch<void>(`/insurance/steps/${stepId}`, {
    method: "DELETE",
    token,
  });
}
