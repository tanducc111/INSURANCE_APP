"use client";

import { FormEvent, useEffect, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  createEmployee,
  listEmployees,
  updateEmployee,
} from "@/services/customer-management-service";
import type { UserStatus } from "@/types/auth";
import type { Employee, EmployeePayload } from "@/types/customer-management";

const emptyForm: EmployeePayload = {
  email: "",
  password: "ChangeMe123!",
  full_name: "",
  status: "active",
  employee_code: "",
  department: "",
  position: "",
  hire_date: "",
};

export default function AdminEmployeesPage() {
  const { isReady, token } = useAdminAccess();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [form, setForm] = useState<EmployeePayload>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadEmployees() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listEmployees(token, { search, limit: 100 });
      setEmployees(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải nhân viên");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadEmployees();
    }
  }, [isReady, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadEmployees();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        department: form.department?.trim() ? form.department : null,
        position: form.position?.trim() ? form.position : null,
        hire_date: form.hire_date || null,
      };
      if (editingId) {
        await updateEmployee(token, editingId, {
          full_name: payload.full_name,
          status: payload.status,
          employee_code: payload.employee_code,
          department: payload.department,
          position: payload.position,
          hire_date: payload.hire_date,
        });
      } else {
        await createEmployee(token, payload);
      }
      setForm(emptyForm);
      setEditingId(null);
      await loadEmployees();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể lưu nhân viên");
    } finally {
      setIsSaving(false);
    }
  }

  function handleEdit(employee: Employee) {
    setEditingId(employee.id);
    setForm({
      email: employee.email,
      password: "",
      full_name: employee.full_name,
      status: employee.status,
      employee_code: employee.employee_code,
      department: employee.department ?? "",
      position: employee.position ?? "",
      hire_date: employee.hire_date ?? "",
    });
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Nhân viên</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 xl:grid-cols-[380px_1fr]">
        <form
          className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={handleSubmit}
        >
          <h2 className="text-lg font-semibold">
            {editingId ? "Chỉnh sửa nhân viên" : "Tạo nhân viên"}
          </h2>
          <div className="mt-5 grid gap-4">
            <input
              className="rounded-md border border-slate-300 px-3 py-2 disabled:bg-slate-100"
              disabled={Boolean(editingId)}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="Email"
              required
              type="email"
              value={form.email}
            />
            {!editingId ? (
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, password: event.target.value })
                }
                placeholder="Mật khẩu ban đầu"
                required
                type="password"
                value={form.password ?? ""}
              />
            ) : null}
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, full_name: event.target.value })
              }
              placeholder="Họ và tên"
              required
              value={form.full_name}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) =>
                setForm({ ...form, employee_code: event.target.value })
              }
              placeholder="Mã nhân viên"
              required
              value={form.employee_code}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, department: event.target.value })
                }
                placeholder="Phòng ban"
                value={form.department ?? ""}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, position: event.target.value })
                }
                placeholder="Chức vụ"
                value={form.position ?? ""}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, hire_date: event.target.value })
                }
                type="date"
                value={form.hire_date ?? ""}
              />
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                onChange={(event) =>
                  setForm({ ...form, status: event.target.value as UserStatus })
                }
                value={form.status}
              >
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Ngừng hoạt động</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button
                className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={isSaving}
                type="submit"
              >
                {isSaving ? "Đang lưu..." : "Lưu"}
              </button>
              {editingId ? (
                <button
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold"
                  onClick={() => {
                    setEditingId(null);
                    setForm(emptyForm);
                  }}
                  type="button"
                >Hủy</button>
              ) : null}
            </div>
          </div>
        </form>

        <section>
          <form className="flex gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm nhân viên"
              value={search}
            />
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >Tìm kiếm</button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
            ) : employees.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                Chưa có nhân viên.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Nhân viên</th>
                      <th className="px-4 py-3">Phòng ban</th>
                      <th className="px-4 py-3">Trạng thái</th>
                      <th className="px-4 py-3">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {employees.map((employee) => (
                      <tr key={employee.id}>
                        <td className="px-4 py-3">
                          <p className="font-semibold">{employee.full_name}</p>
                          <p className="text-xs text-slate-500">
                            {employee.employee_code} - {employee.email}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          {employee.department || "Chưa phân công"}
                        </td>
                        <td className="px-4 py-3"><StatusBadge value={employee.status} /></td>
                        <td className="px-4 py-3">
                          <button
                            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold"
                            onClick={() => handleEdit(employee)}
                            type="button"
                          >Chỉnh sửa</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}
