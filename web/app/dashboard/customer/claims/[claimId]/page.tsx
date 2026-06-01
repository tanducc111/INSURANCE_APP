"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { getCustomerClaim } from "@/services/claim-service";
import type { Claim } from "@/types/claim";

export default function CustomerClaimDetailPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadClaim() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        setClaim(await getCustomerClaim(token, Number(claimId)));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Không thể tải hồ sơ bồi thường");
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadClaim();
    }
  }, [claimId, isReady, token]);

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  if (error || !claim) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {error ?? "Không tìm thấy hồ sơ bồi thường"}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        className="text-sm font-semibold text-ocean hover:text-teal-800"
        href="/dashboard/customer/claims"
      >
          Quay lại hồ sơ bồi thường
      </Link>

      <header className="mt-5 border-b border-slate-200 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium uppercase text-ocean">
              {claim.policy_number}
            </p>
            <h1 className="mt-2 text-3xl font-semibold">{claim.title}</h1>
          </div>
          <ClaimStatusBadge status={claim.status} />
        </div>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Loại</p>
          <p className="mt-2 font-semibold capitalize">
            {formatClaimLabel(claim.incident_type)}
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Ưu tiên</p>
          <p className="mt-2 font-semibold capitalize">{claim.priority}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Ngày</p>
          <p className="mt-2 font-semibold">{claim.incident_date}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Nhân viên</p>
          <p className="mt-2 font-semibold">
            {claim.assigned_employee_name ?? "Chưa phân công"}
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Chi tiết sự cố</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">
          {claim.description}
        </p>
        <p className="mt-4 text-sm font-medium text-slate-500">
          Location: {claim.location || "Chưa cung cấp"}
        </p>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Review Note</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">
          {claim.review_note || "No review note yet."}
        </p>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Tệp đính kèm</h2>
        {claim.attachments.length === 0 ? (
          <p className="mt-3 text-sm font-medium text-slate-500">
            Chưa có tệp đính kèm.
          </p>
        ) : (
          <div className="mt-4 divide-y divide-slate-200">
            {claim.attachments.map((attachment) => (
              <a
                className="block py-3 text-sm font-semibold text-ocean"
                href={attachment.file_url}
                key={attachment.id}
              >
                {attachment.file_name}
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
