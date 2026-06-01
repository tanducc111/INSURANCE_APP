"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  createProcess,
  createStep,
  deleteProcess,
  deleteStep,
  listPackages,
  listProcesses,
  listSteps,
  updateProcess,
  updateStep,
} from "@/services/insurance-service";
import type { UserRole } from "@/types/auth";
import type {
  InsurancePackage,
  InsuranceProcess,
  InsuranceProcessPayload,
  InsuranceStatus,
  ProcessStep,
  ProcessStepPayload,
} from "@/types/insurance";

const emptyProcessForm: InsuranceProcessPayload = {
  package_id: 0,
  name: "",
  description: "",
  status: "active",
};

const emptyStepForm: ProcessStepPayload = {
  step_order: 1,
  name: "",
  description: "",
  required_role: null,
};

export default function AdminInsuranceProcessesPage() {
  const { isReady, token } = useAdminAccess();
  const [packages, setPackages] = useState<InsurancePackage[]>([]);
  const [processes, setProcesses] = useState<InsuranceProcess[]>([]);
  const [steps, setSteps] = useState<ProcessStep[]>([]);
  const [selectedProcessId, setSelectedProcessId] = useState<number | null>(null);
  const [processForm, setProcessForm] =
    useState<InsuranceProcessPayload>(emptyProcessForm);
  const [stepForm, setStepForm] = useState<ProcessStepPayload>(emptyStepForm);
  const [editingProcessId, setEditingProcessId] = useState<number | null>(null);
  const [editingStepId, setEditingStepId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<InsuranceStatus | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isStepLoading, setIsStepLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedProcess = useMemo(
    () => processes.find((process) => process.id === selectedProcessId) ?? null,
    [processes, selectedProcessId],
  );

  function packageName(packageId: number) {
    return (
      packages.find((packageItem) => packageItem.id === packageId)?.name ??
      `Package ${packageId}`
    );
  }

  async function loadProcesses() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [packageData, processData] = await Promise.all([
        listPackages(token, { limit: 100 }),
        listProcesses(token, { search, status: statusFilter, limit: 100 }),
      ]);
      setPackages(packageData);
      setProcesses(processData);
      setProcessForm((current) => ({
        ...current,
        package_id: current.package_id || packageData[0]?.id || 0,
      }));
      setSelectedProcessId((current) => {
        if (current && processData.some((process) => process.id === current)) {
          return current;
        }
        return processData[0]?.id ?? null;
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải quy trình bảo hiểm");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadSteps(processId: number) {
    if (!token) {
      return;
    }

    setIsStepLoading(true);
    setError(null);
    try {
      const data = await listSteps(token, processId, { limit: 100 });
      setSteps(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải bước xử lý");
    } finally {
      setIsStepLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadProcesses();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedProcessId) {
      void loadSteps(selectedProcessId);
    } else {
      setSteps([]);
    }
  }, [selectedProcessId, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadProcesses();
  }

  async function handleProcessSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !processForm.package_id) {
      return;
    }

    setError(null);
    try {
      const payload = {
        ...processForm,
        description: processForm.description?.trim()
          ? processForm.description
          : null,
      };
      if (editingProcessId) {
        await updateProcess(token, editingProcessId, payload);
      } else {
        await createProcess(token, payload);
      }
      setEditingProcessId(null);
      setProcessForm({
        ...emptyProcessForm,
        package_id: packages[0]?.id || 0,
      });
      await loadProcesses();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể lưu quy trình bảo hiểm");
    }
  }

  function handleEditProcess(process: InsuranceProcess) {
    setEditingProcessId(process.id);
    setProcessForm({
      package_id: process.package_id,
      name: process.name,
      description: process.description ?? "",
      status: process.status,
    });
  }

  async function handleDeleteProcess(processId: number) {
    if (!token || !window.confirm("Xóa quy trình này?")) {
      return;
    }
    await deleteProcess(token, processId);
    setSelectedProcessId(null);
    await loadProcesses();
  }

  async function handleStepSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedProcessId) {
      return;
    }

    setError(null);
    try {
      const payload = {
        ...stepForm,
        description: stepForm.description?.trim() ? stepForm.description : null,
        required_role: stepForm.required_role || null,
      };
      if (editingStepId) {
        await updateStep(token, editingStepId, payload);
      } else {
        await createStep(token, selectedProcessId, payload);
      }
      setEditingStepId(null);
      setStepForm({
        ...emptyStepForm,
        step_order: steps.length + 1,
      });
      await loadSteps(selectedProcessId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể lưu bước xử lý");
    }
  }

  function handleEditStep(step: ProcessStep) {
    setEditingStepId(step.id);
    setStepForm({
      step_order: step.step_order,
      name: step.name,
      description: step.description ?? "",
      required_role: step.required_role,
    });
  }

  async function handleDeleteStep(stepId: number) {
    if (!token || !selectedProcessId || !window.confirm("Xóa bước này?")) {
      return;
    }
    await deleteStep(token, stepId);
    await loadSteps(selectedProcessId);
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Quy trình bảo hiểm</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 xl:grid-cols-[380px_1fr]">
        <div className="space-y-6">
          <form
            className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
            onSubmit={handleProcessSubmit}
          >
            <h2 className="text-lg font-semibold">
              {editingProcessId ? "Chỉnh sửa quy trình" : "Tạo quy trình"}
            </h2>
            <div className="mt-5 grid gap-4">
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                disabled={packages.length === 0}
                onChange={(event) =>
                  setProcessForm({
                    ...processForm,
                    package_id: Number(event.target.value),
                  })
                }
                required
                value={processForm.package_id}
              >
                {packages.length === 0 ? (
                <option value={0}>Chưa có gói bảo hiểm</option>
                ) : (
                  packages.map((packageItem) => (
                    <option key={packageItem.id} value={packageItem.id}>
                      {packageItem.name}
                    </option>
                  ))
                )}
              </select>
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setProcessForm({ ...processForm, name: event.target.value })
                }
                placeholder="Process name"
                required
                value={processForm.name}
              />
              <textarea
                className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setProcessForm({
                    ...processForm,
                    description: event.target.value,
                  })
                }
                placeholder="Mô tả"
                value={processForm.description ?? ""}
              />
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setProcessForm({
                    ...processForm,
                    status: event.target.value as InsuranceStatus,
                  })
                }
                value={processForm.status}
              >
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Ngừng hoạt động</option>
              </select>
              <div className="flex gap-3">
                <button
                  className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                  disabled={packages.length === 0}
                  type="submit"
                >Lưu</button>
                {editingProcessId ? (
                  <button
                    className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                    onClick={() => {
                      setEditingProcessId(null);
                      setProcessForm({
                        ...emptyProcessForm,
                        package_id: packages[0]?.id || 0,
                      });
                    }}
                    type="button"
                  >Hủy</button>
                ) : null}
              </div>
            </div>
          </form>

          <form
            className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
            onSubmit={handleStepSubmit}
          >
            <h2 className="text-lg font-semibold">
              {editingStepId ? "Chỉnh sửa bước" : "Thêm bước"}
            </h2>
            <div className="mt-5 grid gap-4">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                min="1"
                onChange={(event) =>
                  setStepForm({
                    ...stepForm,
                    step_order: Number(event.target.value),
                  })
                }
                placeholder="Order"
                required
                type="number"
                value={stepForm.step_order}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setStepForm({ ...stepForm, name: event.target.value })
                }
                placeholder="Step name"
                required
                value={stepForm.name}
              />
              <textarea
                className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setStepForm({ ...stepForm, description: event.target.value })
                }
                placeholder="Mô tả"
                value={stepForm.description ?? ""}
              />
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setStepForm({
                    ...stepForm,
                    required_role: event.target.value
                      ? (event.target.value as UserRole)
                      : null,
                  })
                }
                value={stepForm.required_role ?? ""}
              >
                <option value="">Any role</option>
                <option value="ADMIN">Quản trị</option>
                <option value="EMPLOYEE">Nhân viên</option>
                <option value="CUSTOMER">Khách hàng</option>
              </select>
              <div className="flex gap-3">
                <button
                  className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                  disabled={!selectedProcessId}
                  type="submit"
                >Lưu</button>
                {editingStepId ? (
                  <button
                    className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                    onClick={() => {
                      setEditingStepId(null);
                      setStepForm(emptyStepForm);
                    }}
                    type="button"
                  >Hủy</button>
                ) : null}
              </div>
            </div>
          </form>
        </div>

        <section>
          <form className="flex flex-wrap gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm quy trình"
              value={search}
            />
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setStatusFilter(event.target.value as InsuranceStatus | "all")
              }
              value={statusFilter}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="inactive">Ngừng hoạt động</option>
            </select>
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >Tìm kiếm</button>
          </form>

          <div className="mt-5 grid gap-6 lg:grid-cols-[1fr_360px]">
            <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
              {isLoading ? (
                <p className="p-5 text-sm font-medium text-slate-500">
                  Đang tải...
                </p>
              ) : processes.length === 0 ? (
                <p className="p-5 text-sm font-medium text-slate-500">
                  Chưa có quy trình.
                </p>
              ) : (
                <div className="divide-y divide-slate-200">
                  {processes.map((process) => (
                    <div
                      className={`px-5 py-4 transition ${
                        selectedProcessId === process.id
                          ? "bg-teal-50"
                          : "hover:bg-slate-50"
                      }`}
                      key={process.id}
                    >
                      <button
                        className="block w-full text-left"
                        onClick={() => setSelectedProcessId(process.id)}
                        type="button"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="font-semibold">{process.name}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              {packageName(process.package_id)}
                            </p>
                          </div>
                          <p className="text-sm font-semibold capitalize text-ocean">
                            <StatusBadge value={process.status} />
                          </p>
                        </div>
                      </button>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                          onClick={() => handleEditProcess(process)}
                          type="button"
                        >Chỉnh sửa</button>
                        <button
                          className="rounded-md border border-red-300 px-3 py-1 text-xs font-semibold text-red-700"
                          onClick={() => void handleDeleteProcess(process.id)}
                          type="button"
                        >
                          Xóa
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">
                {selectedProcess ? selectedProcess.name : "Process Steps"}
              </h2>
              {isStepLoading ? (
                <p className="mt-5 text-sm font-medium text-slate-500">
                  Đang tải...
                </p>
              ) : steps.length === 0 ? (
                <p className="mt-5 text-sm font-medium text-slate-500">
                  Chưa có bước xử lý.
                </p>
              ) : (
                <div className="mt-5 space-y-3">
                  {steps.map((step) => (
                    <div
                      className="rounded-md border border-slate-200 p-4"
                      key={step.id}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold">
                            {step.step_order}. {step.name}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {step.required_role ?? "Any role"}
                          </p>
                        </div>
                      </div>
                      {step.description ? (
                        <p className="mt-3 text-sm text-slate-600">
                          {step.description}
                        </p>
                      ) : null}
                      <div className="mt-3 flex gap-2">
                        <button
                          className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                          onClick={() => handleEditStep(step)}
                          type="button"
                        >Chỉnh sửa</button>
                        <button
                          className="rounded-md border border-red-300 px-3 py-1 text-xs font-semibold text-red-700"
                          onClick={() => void handleDeleteStep(step.id)}
                          type="button"
                        >
                          Xóa
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      </section>
    </div>
  );
}
