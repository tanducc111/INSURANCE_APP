"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import { getPackage, listProcesses } from "@/services/insurance-service";
import type { InsurancePackage, InsuranceProcess } from "@/types/insurance";

export default function AdminInsurancePackageDetailPage() {
  const { packageId } = useParams<{ packageId: string }>();
  const { isReady, token } = useAdminAccess();
  const [packageItem, setPackageItem] = useState<InsurancePackage | null>(null);
  const [processes, setProcesses] = useState<InsuranceProcess[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetail() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const id = Number(packageId);
        const [packageData, processData] = await Promise.all([
          getPackage(token, id),
          listProcesses(token, { packageId: id, limit: 100 }),
        ]);
        setPackageItem(packageData);
        setProcesses(processData);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Không thể tải gói bảo hiểm");
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadDetail();
    }
  }, [isReady, packageId, token]);

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  if (error || !packageItem) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {error ?? "Package not found"}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        className="text-sm font-semibold text-ocean hover:text-teal-800"
        href="/dashboard/admin/insurance/packages"
      >
        Back to packages
      </Link>

      <header className="mt-5 border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">
          {packageItem.code}
        </p>
        <h1 className="mt-2 text-3xl font-semibold">{packageItem.name}</h1>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Loại</p>
          <p className="mt-2 font-semibold">{packageItem.package_type}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Phí bảo hiểm</p>
          <p className="mt-2 font-semibold">{packageItem.premium_amount}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Quyền lợi bảo hiểm</p>
          <p className="mt-2 font-semibold">{packageItem.coverage_amount}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Trạng thái</p>
          <div className="mt-2"><StatusBadge value={packageItem.status} /></div>
        </div>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Mô tả</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          {packageItem.description || "Chưa có mô tả."}
        </p>
      </section>

      <section className="mt-6 rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Quy trình</h2>
        {processes.length === 0 ? (
          <p className="mt-4 text-sm font-medium text-slate-500">
            Chưa có quy trình.
          </p>
        ) : (
          <div className="mt-4 divide-y divide-slate-200">
            {processes.map((process) => (
              <div className="py-3" key={process.id}>
                <p className="font-semibold">{process.name}</p>
                <p className="mt-1 text-sm text-slate-500 capitalize">
                  <StatusBadge value={process.status} />
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
