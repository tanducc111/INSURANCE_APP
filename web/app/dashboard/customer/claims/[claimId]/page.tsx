"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ClaimAttachments } from "@/components/claims/claim-attachments";
import {
  ClaimStatusBadge,
  formatClaimLabel,
} from "@/components/claims/claim-status-badge";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  deleteCustomerClaimAttachment,
  getCustomerClaim,
} from "@/services/claim-service";
import type { Claim, ClaimAttachment } from "@/types/claim";

export default function CustomerClaimDetailPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
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
        setError(
          err instanceof ApiError
            ? err.message
            : "Không thể tải hồ sơ bồi thường",
        );
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadClaim();
    }
  }, [claimId, isReady, token]);

  async function handleDeleteAttachment(attachment: ClaimAttachment) {
    if (!token || !claim) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await deleteCustomerClaimAttachment(token, claim.id, attachment.id);
      setClaim({
        ...claim,
        attachments: claim.attachments.filter(
          (current) => current.id !== attachment.id,
        ),
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể xóa tệp đính kèm");
    } finally {
      setIsDeleting(false);
    }
  }

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
          <p className="mt-2 font-semibold capitalize">{formatClaimLabel(claim.priority)}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">
            Ngày xảy ra
          </p>
          <p className="mt-2 font-semibold">{claim.incident_date}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">
            Nhân viên
          </p>
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
          Địa điểm: {claim.location || "Chưa cung cấp"}
        </p>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Ghi chú thẩm định</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">
          {claim.review_note || "Chưa có ghi chú thẩm định."}
        </p>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Tệp đính kèm</h2>
          <p className="text-xs font-medium text-slate-500">
            Hóa đơn viện phí, ảnh tai nạn, biên lai sửa chữa hoặc giấy tờ liên quan
          </p>
        </div>
        <ClaimAttachments
          attachments={claim.attachments}
          isDeleting={isDeleting}
          onDelete={
            claim.status === "pending" || claim.status === "need_more_documents"
              ? handleDeleteAttachment
              : undefined
          }
        />
      </section>
    </div>
  );
}
