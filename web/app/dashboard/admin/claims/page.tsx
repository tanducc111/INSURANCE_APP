"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { SearchFilterBar } from "@/components/ui/search-filter-bar";
import { StatusBadge, statusLabel } from "@/components/ui/status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  assignAdminClaim,
  listAdminClaims,
  updateAdminClaimStatus,
} from "@/services/claim-service";
import { listEmployees } from "@/services/customer-management-service";
import type {
  Claim,
  ClaimIncidentType,
  ClaimPriority,
  ClaimStatus,
} from "@/types/claim";
import type { Employee } from "@/types/customer-management";

export default function AdminClaimsPage() {
  const { isReady, token } = useAdminAccess();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<ClaimIncidentType | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<ClaimPriority | "all">(
    "all",
  );
  const [nextStatus, setNextStatus] = useState<ClaimStatus>("reviewing");
  const [assignedEmployeeValue, setAssignedEmployeeValue] = useState("none");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedClaim =
    claims.find((claim) => claim.id === selectedClaimId) ?? null;

  async function loadData() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [claimData, employeeData] = await Promise.all([
        listAdminClaims(token, {
          search,
          status: statusFilter,
          incidentType: typeFilter,
          priority: priorityFilter,
          limit: 100,
        }),
        listEmployees(token, { limit: 100 }),
      ]);
      setClaims(claimData);
      setEmployees(employeeData);
      setSelectedClaimId((current) =>
        claimData.some((claim) => claim.id === current)
          ? current
          : claimData[0]?.id ?? null,
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể tải hồ sơ bồi thường",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadData();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedClaim) {
      setNextStatus(selectedClaim.status);
      setAssignedEmployeeValue(
        selectedClaim.assigned_employee_id
          ? String(selectedClaim.assigned_employee_id)
          : "none",
      );
    }
  }, [selectedClaim?.id]);

  function replaceClaim(updatedClaim: Claim) {
    setClaims((current) =>
      current.map((claim) =>
        claim.id === updatedClaim.id ? updatedClaim : claim,
      ),
    );
    setSelectedClaimId(updatedClaim.id);
  }

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadData();
  }

  async function handleStatusSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(await updateAdminClaimStatus(token, selectedClaim.id, nextStatus));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể cập nhật trạng thái",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAssignmentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(
        await assignAdminClaim(
          token,
          selectedClaim.id,
          assignedEmployeeValue === "none" ? null : Number(assignedEmployeeValue),
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể phân công hồ sơ",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady) {
    return <LoadingState />;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        description="Theo dõi, phân công và cập nhật tiến độ xử lý hồ sơ bồi thường."
        eyebrow="Quản trị"
        title="Bồi thường"
      />

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <div className="mt-6">
        <SearchFilterBar
          onSubmit={handleFilter}
          search={search}
          searchPlaceholder="Tìm kiếm hồ sơ bồi thường"
          setSearch={setSearch}
        >
        <select
          className="rounded-md border border-border px-3 py-2 text-sm"
          onChange={(event) =>
            setStatusFilter(event.target.value as ClaimStatus | "all")
          }
          value={statusFilter}
        >
          <option value="all">Tất cả trạng thái</option>
          <option value="pending">Chờ xử lý</option>
          <option value="reviewing">Đang xem xét</option>
          <option value="need_more_documents">Cần bổ sung hồ sơ</option>
          <option value="approved">Đã duyệt</option>
          <option value="rejected">Từ chối</option>
          <option value="completed">Hoàn tất</option>
        </select>
        <select
          className="rounded-md border border-border px-3 py-2 text-sm"
          onChange={(event) =>
            setTypeFilter(event.target.value as ClaimIncidentType | "all")
          }
          value={typeFilter}
        >
          <option value="all">Tất cả loại sự cố</option>
          <option value="accident">Tai nạn</option>
          <option value="hospital">Nằm viện</option>
          <option value="damage">Thiệt hại tài sản</option>
          <option value="other">Khác</option>
        </select>
        <select
          className="rounded-md border border-border px-3 py-2 text-sm"
          onChange={(event) =>
            setPriorityFilter(event.target.value as ClaimPriority | "all")
          }
          value={priorityFilter}
        >
          <option value="all">Tất cả mức ưu tiên</option>
          <option value="low">Thấp</option>
          <option value="medium">Trung bình</option>
          <option value="high">Cao</option>
          <option value="urgent">Khẩn cấp</option>
        </select>
        <button
          className="rounded-md bg-primary px-4 py-2 text-sm font-bold text-white"
          type="submit"
        >
          Lọc
        </button>
        </SearchFilterBar>
      </div>

      <section className="mt-5 grid gap-6 xl:grid-cols-[1fr_420px]">
        <DataTable>
          {isLoading ? (
            <LoadingState />
          ) : claims.length === 0 ? (
            <EmptyState title="Chưa có hồ sơ bồi thường" />
          ) : (
              <table className="w-full min-w-[960px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-muted">
                  <tr>
                    <th className="px-4 py-3">Hồ sơ</th>
                    <th className="px-4 py-3">Khách hàng</th>
                    <th className="px-4 py-3">Hợp đồng</th>
                    <th className="px-4 py-3">Nhân viên</th>
                    <th className="px-4 py-3">Ưu tiên</th>
                    <th className="px-4 py-3">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {claims.map((claim) => (
                    <tr
                      className={`cursor-pointer ${
                        selectedClaimId === claim.id ? "bg-blue-50" : ""
                      }`}
                      key={claim.id}
                      onClick={() => setSelectedClaimId(claim.id)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold">{claim.title}</p>
                        <p className="text-xs capitalize text-slate-500">
                          {formatClaimLabel(claim.incident_type)}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold">{claim.customer_name}</p>
                        <p className="text-xs text-slate-500">
                          {claim.customer_code}
                        </p>
                      </td>
                      <td className="px-4 py-3">{claim.policy_number}</td>
                      <td className="px-4 py-3">
                        {claim.assigned_employee_name ?? "Chưa phân công"}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge value={claim.priority} />
                      </td>
                      <td className="px-4 py-3">
                        <ClaimStatusBadge status={claim.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
          )}
        </DataTable>

        <aside className="rounded-lg border border-border bg-white p-5 shadow-sm">
          {selectedClaim ? (
            <div className="space-y-5">
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-semibold">{selectedClaim.title}</h2>
                  <ClaimStatusBadge status={selectedClaim.status} />
                </div>
                <p className="mt-2 text-sm text-slate-500">
                  {selectedClaim.customer_name} - {selectedClaim.package_name}
                </p>
              </div>

              <div className="space-y-3 border-l-2 border-blue-100 pl-4">
                {[
                  ["Tiếp nhận", "pending"],
                  ["Xem xét", "reviewing"],
                  ["Quyết định", selectedClaim.status],
                ].map(([label, status]) => (
                  <div className="relative" key={`${label}-${status}`}>
                    <span className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-primary" />
                    <p className="text-sm font-bold text-ink">{label}</p>
                    <p className="text-xs text-muted">{statusLabel(status)}</p>
                  </div>
                ))}
              </div>

              <div className="grid gap-2 text-sm text-slate-600">
                <p>Hợp đồng bảo hiểm: {selectedClaim.policy_number}</p>
                <p>Ngày xảy ra: {selectedClaim.incident_date}</p>
                <p>Địa điểm: {selectedClaim.location || "Chưa cung cấp"}</p>
                <p>Loại sự cố: {formatClaimLabel(selectedClaim.incident_type)}</p>
              </div>

              <p className="text-sm leading-6 text-slate-700">
                {selectedClaim.description}
              </p>

              <form className="grid gap-3" onSubmit={handleStatusSubmit}>
                <select
                  className="rounded-md border border-slate-300 px-3 py-2"
                  onChange={(event) =>
                    setNextStatus(event.target.value as ClaimStatus)
                  }
                  value={nextStatus}
                >
                  <option value="pending">Chờ xử lý</option>
                  <option value="reviewing">Đang xem xét</option>
                  <option value="need_more_documents">Cần bổ sung hồ sơ</option>
                  <option value="approved">Đã duyệt</option>
                  <option value="rejected">Từ chối</option>
                  <option value="completed">Hoàn tất</option>
                </select>
                <button
                  className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                  disabled={isSaving}
                  type="submit"
                >
                  {isSaving ? "Đang lưu..." : "Cập nhật trạng thái"}
                </button>
              </form>

              <form className="grid gap-3" onSubmit={handleAssignmentSubmit}>
                <select
                  className="rounded-md border border-slate-300 px-3 py-2"
                  onChange={(event) => setAssignedEmployeeValue(event.target.value)}
                  value={assignedEmployeeValue}
                >
                  <option value="none">Chưa phân công</option>
                  {employees.map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.full_name} ({employee.employee_code})
                    </option>
                  ))}
                </select>
                <button
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:bg-slate-100"
                  disabled={isSaving}
                  type="submit"
                >
                  {isSaving ? "Đang lưu..." : "Phân công nhân viên"}
                </button>
              </form>

              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">
                  Ghi chú thẩm định
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {selectedClaim.review_note || "Chưa có ghi chú thẩm định."}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">
                  Tệp đính kèm
                </h3>
                {selectedClaim.attachments.length === 0 ? (
                  <p className="mt-3 text-sm font-medium text-slate-500">
                    Chưa có tệp đính kèm.
                  </p>
                ) : (
                  <div className="mt-3 divide-y divide-slate-200">
                    {selectedClaim.attachments.map((attachment) => (
                      <a
                        className="block py-2 text-sm font-semibold text-ocean"
                        href={attachment.file_url}
                        key={attachment.id}
                      >
                        {attachment.file_name}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-500">
              Chọn một hồ sơ để xử lý.
            </p>
          )}
        </aside>
      </section>
    </div>
  );
}
