"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { listCustomerClaims } from "@/services/claim-service";
import type {
  Claim,
  ClaimIncidentType,
  ClaimPriority,
  ClaimStatus,
} from "@/types/claim";

export default function CustomerClaimsPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<ClaimIncidentType | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<ClaimPriority | "all">(
    "all",
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadClaims() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setClaims(
        await listCustomerClaims(token, {
          status: statusFilter,
          incidentType: typeFilter,
          priority: priorityFilter,
          limit: 100,
        }),
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

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadClaims();
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Khách hàng</p>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-semibold">Hồ sơ bồi thường của tôi</h1>
          <Link
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white"
            href="/dashboard/customer/report-incident"
          >
            Báo cáo sự cố
          </Link>
        </div>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form className="mt-6 flex flex-wrap gap-3" onSubmit={handleFilter}>
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

      <section className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        {isLoading ? (
          <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
        ) : claims.length === 0 ? (
          <p className="p-5 text-sm font-medium text-slate-500">
            Chưa có hồ sơ bồi thường.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Hồ sơ</th>
                  <th className="px-4 py-3">Hợp đồng</th>
                    <th className="px-4 py-3">Loại sự cố</th>
                  <th className="px-4 py-3">Ưu tiên</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {claims.map((claim) => (
                  <tr key={claim.id}>
                    <td className="px-4 py-3">
                      <p className="font-semibold">{claim.title}</p>
                      <p className="text-xs text-slate-500">
                        {claim.package_name}
                      </p>
                    </td>
                    <td className="px-4 py-3">{claim.policy_number}</td>
                    <td className="px-4 py-3 capitalize">
                      {formatClaimLabel(claim.incident_type)}
                    </td>
                    <td className="px-4 py-3 capitalize">{claim.priority}</td>
                    <td className="px-4 py-3">
                      <ClaimStatusBadge status={claim.status} />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                        href={`/dashboard/customer/claims/${claim.id}`}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
