"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { FileText, UploadCloud, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import {
  createCustomerClaim,
  uploadCustomerClaimAttachments,
} from "@/services/claim-service";
import { listCustomerSubscriptions } from "@/services/subscription-service";
import type {
  ClaimIncidentType,
  ClaimPayload,
  ClaimPriority,
} from "@/types/claim";
import type { CustomerInsuranceSubscription } from "@/types/subscription";

const allowedFileTypes = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
];
const maxFileSize = 5 * 1024 * 1024;

const emptyForm: ClaimPayload = {
  subscription_id: 0,
  title: "",
  description: "",
  incident_type: "accident",
  incident_date: "",
  location: "",
  priority: "medium",
  attachments: [],
};

function formatFileSize(size: number) {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export default function CustomerReportIncidentPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [subscriptions, setSubscriptions] = useState<
    CustomerInsuranceSubscription[]
  >([]);
  const [form, setForm] = useState<ClaimPayload>(emptyForm);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSubscriptions() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await listCustomerSubscriptions(token, { limit: 100 });
        setSubscriptions(data);
        setForm((current) => ({
          ...current,
          subscription_id: current.subscription_id || data[0]?.id || 0,
        }));
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Không thể tải hợp đồng bảo hiểm",
        );
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadSubscriptions();
    }
  }, [isReady, token]);

  function handleFileSelect(files: FileList | null) {
    if (!files) {
      return;
    }

    const incomingFiles = Array.from(files);
    const invalidType = incomingFiles.find(
      (file) => !allowedFileTypes.includes(file.type),
    );
    if (invalidType) {
      setError(
        "Định dạng tệp không được hỗ trợ. Vui lòng tải lên JPG, PNG, WEBP hoặc PDF.",
      );
      return;
    }

    const oversized = incomingFiles.find((file) => file.size > maxFileSize);
    if (oversized) {
      setError("Tệp quá lớn. Vui lòng tải lên tệp nhỏ hơn 5MB.");
      return;
    }

    setError(null);
    setSelectedFiles((current) => [...current, ...incomingFiles]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function removeSelectedFile(index: number) {
    setSelectedFiles((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !form.subscription_id) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const claim = await createCustomerClaim(token, {
        ...form,
        location: form.location?.trim() ? form.location : null,
        attachments: [],
      });
      if (selectedFiles.length > 0) {
        await uploadCustomerClaimAttachments(token, claim.id, selectedFiles);
      }
      router.push(`/dashboard/customer/claims/${claim.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Không thể gửi hồ sơ bồi thường",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Khách hàng</p>
        <h1 className="mt-2 text-3xl font-semibold">Báo cáo sự cố</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <form
        className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm"
        onSubmit={handleSubmit}
      >
        <div className="grid gap-4">
          <label className="grid gap-2 text-sm font-semibold text-slate-700">
            Hợp đồng bảo hiểm
            <select
              className="rounded-md border border-slate-300 px-3 py-2 font-normal"
              disabled={subscriptions.length === 0}
              onChange={(event) =>
                setForm({ ...form, subscription_id: Number(event.target.value) })
              }
              required
              value={form.subscription_id}
            >
              {subscriptions.length === 0 ? (
                <option value={0}>Chưa có hợp đồng bảo hiểm</option>
              ) : (
                subscriptions.map((subscription) => (
                  <option key={subscription.id} value={subscription.id}>
                    {subscription.policy_number} - {subscription.package_name}
                  </option>
                ))
              )}
            </select>
          </label>

          <input
            className="rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            placeholder="Tiêu đề hồ sơ bồi thường"
            required
            value={form.title}
          />

          <textarea
            className="min-h-32 rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
            placeholder="Mô tả sự cố"
            required
            value={form.description}
          />

          <div className="grid gap-4 md:grid-cols-2">
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({
                  ...form,
                  incident_type: event.target.value as ClaimIncidentType,
                })
              }
              value={form.incident_type}
            >
              <option value="accident">Tai nạn</option>
              <option value="hospital">Nằm viện</option>
              <option value="damage">Thiệt hại tài sản</option>
              <option value="other">Khác</option>
            </select>

            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({
                  ...form,
                  priority: event.target.value as ClaimPriority,
                })
              }
              value={form.priority}
            >
              <option value="low">Thấp</option>
              <option value="medium">Trung bình</option>
              <option value="high">Cao</option>
              <option value="urgent">Khẩn cấp</option>
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, incident_date: event.target.value })
              }
              required
              type="date"
              value={form.incident_date}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, location: event.target.value })
              }
              placeholder="Địa điểm"
              value={form.location ?? ""}
            />
          </div>

          <section className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  Tệp đính kèm
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Tải lên hóa đơn viện phí, ảnh tai nạn, biên lai sửa chữa hoặc
                  giấy tờ liên quan.
                </p>
              </div>
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white">
                <UploadCloud className="h-4 w-4" aria-hidden="true" />
                Chọn tệp
                <input
                  accept=".jpg,.jpeg,.png,.webp,.pdf"
                  className="sr-only"
                  multiple
                  onChange={(event) => handleFileSelect(event.target.files)}
                  ref={fileInputRef}
                  type="file"
                />
              </label>
            </div>

            <p className="mt-3 text-xs font-medium text-slate-500">
              Hỗ trợ JPG, PNG, WEBP hoặc PDF. Mỗi tệp tối đa 5MB.
            </p>

            {selectedFiles.length > 0 ? (
              <div className="mt-4 grid gap-2">
                {selectedFiles.map((file, index) => (
                  <div
                    className="flex items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2"
                    key={`${file.name}-${file.size}-${index}`}
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-ocean" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900">
                          {file.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-700"
                      onClick={() => removeSelectedFile(index)}
                      type="button"
                    >
                      <X className="h-3.5 w-3.5" aria-hidden="true" />
                      Xóa tệp
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
          </section>

          <button
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={isSaving || subscriptions.length === 0}
            type="submit"
          >
            {isSaving ? "Đang gửi..." : "Gửi hồ sơ bồi thường"}
          </button>
        </div>
      </form>
    </div>
  );
}
