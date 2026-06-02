"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { ClaimAttachments } from "@/components/claims/claim-attachments";
import { StatusBadge } from "@/components/ui/status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  addEmployeeReviewNote,
  listEmployeeClaims,
  updateEmployeeClaimStatus,
} from "@/services/claim-service";
import type {
  Claim,
  ClaimIncidentType,
  ClaimPriority,
  ClaimStatus,
} from "@/types/claim";

export default function EmployeeClaimsPage() {
  const { isReady, token } = useRoleAccess(["EMPLOYEE"]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<ClaimIncidentType | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<ClaimPriority | "all">(
    "all",
  );
  const [nextStatus, setNextStatus] = useState<ClaimStatus>("reviewing");
  const [reviewNote, setReviewNote] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedClaim =
    claims.find((claim) => claim.id === selectedClaimId) ?? null;

  async function loadClaims() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listEmployeeClaims(token, {
        search,
        status: statusFilter,
        incidentType: typeFilter,
        priority: priorityFilter,
        limit: 100,
      });
      setClaims(data);
      setSelectedClaimId((current) =>
        data.some((claim) => claim.id === current) ? current : data[0]?.id ?? null,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải hồ sơ bồi thường");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadClaims();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedClaim) {
      setNextStatus(selectedClaim.status);
      setReviewNote(selectedClaim.review_note ?? "");
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
    await loadClaims();
  }

  async function handleStatusSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(
        await updateEmployeeClaimStatus(token, selectedClaim.id, nextStatus),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể cập nhật trạng thái");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleNoteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedClaim) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      replaceClaim(
        await addEmployeeReviewNote(token, selectedClaim.id, reviewNote),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể lưu ghi chú");
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Nhân viên</p>
        <h1 className="mt-2 text-3xl font-semibold">Xử lý bồi thường</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form className="mt-6 flex flex-wrap gap-3" onSubmit={handleFilter}>
        <input
          className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Tìm kiếm hồ sơ bồi thường"
          value={search}
        />
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
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
          className="rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            setTypeFilter(event.target.value as ClaimIncidentType | "all")
          }
          value={typeFilter}
        >
          <option value="all">Tất cả loại sự cố</option>
          <option value="accident">Tai nạn</option>
          <option value="hospital">Nằm viện</option>
          <option value="damage">Thiệt hại</option>
          <option value="other">Khác</option>
        </select>
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
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
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
          type="submit"
        >
          Lọc
        </button>
      </form>

      <section className="mt-5 grid gap-6 xl:grid-cols-[1fr_420px]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
          ) : claims.length === 0 ? (
            <p className="p-5 text-sm font-medium text-slate-500">
              Chưa có hồ sơ bồi thường từ khách hàng được phân công.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Hồ sơ</th>
                    <th className="px-4 py-3">Khách hàng</th>
                    <th className="px-4 py-3">Loại sự cố</th>
                    <th className="px-4 py-3">Ưu tiên</th>
                    <th className="px-4 py-3">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {claims.map((claim) => (
                    <tr
                      className={`cursor-pointer ${
                        selectedClaimId === claim.id ? "bg-teal-50" : ""
                      }`}
                      key={claim.id}
                      onClick={() => setSelectedClaimId(claim.id)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold">{claim.title}</p>
                        <p className="text-xs text-slate-500">
                          {claim.policy_number}
                        </p>
                      </td>
                      <td className="px-4 py-3">{claim.customer_name}</td>
                      <td className="px-4 py-3 capitalize">
                        {formatClaimLabel(claim.incident_type)}
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
            </div>
          )}
        </div>

        <aside className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
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

              <div className="grid gap-2 text-sm text-slate-600">
                <p>Hợp đồng bảo hiểm: {selectedClaim.policy_number}</p>
                <p>Ngày xảy ra: {selectedClaim.incident_date}</p>
                <p>Địa điểm: {selectedClaim.location || "Chưa cung cấp"}</p>
                <p className="capitalize">
                  Loại sự cố: {formatClaimLabel(selectedClaim.incident_type)}
                </p>
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

              <form className="grid gap-3" onSubmit={handleNoteSubmit}>
                <textarea
                  className="min-h-28 rounded-md border border-slate-300 px-3 py-2"
                  onChange={(event) => setReviewNote(event.target.value)}
                  placeholder="Ghi chú thẩm định"
                  required
                  value={reviewNote}
                />
                <button
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:bg-slate-100"
                  disabled={isSaving}
                  type="submit"
                >
                  {isSaving ? "Đang lưu..." : "Lưu ghi chú thẩm định"}
                </button>
              </form>

              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">
                  Chứng từ khách hàng đã gửi
                </h3>
                <div className="mt-3">
                  <ClaimAttachments attachments={selectedClaim.attachments} />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-500">
              Chọn hồ sơ để thẩm định.
            </p>
          )}
        </aside>
      </section>
    </div>
  );
}
