"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowLeft, LockKeyhole, ShieldCheck } from "lucide-react";

import { setStoredAuth } from "@/lib/auth-storage";
import { ApiError } from "@/services/api-client";
import { login } from "@/services/auth-service";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@insurance.local");
  const [password, setPassword] = useState("11111111");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await login(email, password);
      setStoredAuth(response.access_token, response.user);
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể đăng nhập. Vui lòng thử lại.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-mist px-6 py-10 text-ink lg:grid-cols-[1fr_520px]">
      <section className="hidden flex-col justify-between rounded-lg border border-border bg-primary p-10 text-white shadow-soft lg:flex">
        <div>
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white/15">
            <ShieldCheck aria-hidden className="h-6 w-6" />
          </div>
          <p className="mt-6 text-sm font-bold uppercase tracking-normal text-blue-100">
            Bảo hiểm Việt
          </p>
          <h1 className="mt-4 max-w-xl text-5xl font-extrabold leading-tight">
            Không gian vận hành bảo hiểm hiện đại và bảo mật
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-blue-100">
            Quản lý khách hàng, hợp đồng, bồi thường, lịch hẹn và tài liệu tri
            thức doanh nghiệp trong một nền tảng thống nhất.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {["Hợp đồng", "Bồi thường", "Hỗ trợ"].map((item) => (
            <div className="rounded-lg bg-white/10 p-4" key={item}>
              <p className="text-sm font-bold">{item}</p>
              <p className="mt-2 text-xs text-blue-100">Theo dõi tức thời</p>
            </div>
          ))}
        </div>
      </section>

      <section className="flex items-center justify-center lg:px-10">
        <div className="w-full max-w-md rounded-lg border border-border bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-primary">
              <LockKeyhole aria-hidden className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-bold text-primary">Truy cập bảo mật</p>
              <h1 className="text-2xl font-extrabold">Đăng nhập</h1>
            </div>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-sm font-bold text-slate-700">Email</span>
              <input
                className="mt-2 w-full rounded-md border border-border px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
                name="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="ten@congty.vn"
                required
                type="email"
                value={email}
              />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-slate-700">Mật khẩu</span>
              <input
                className="mt-2 w-full rounded-md border border-border px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Nhập mật khẩu"
                required
                type="password"
                value={password}
              />
            </label>

            {error ? (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">
                {error}
              </p>
            ) : null}

            <button
              className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>

          <Link
            className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-primary hover:text-blue-700"
            href="/"
          >
            <ArrowLeft aria-hidden className="h-4 w-4" />
            Quay về trang chủ
          </Link>
        </div>
      </section>
    </main>
  );
}
