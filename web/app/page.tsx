import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-mist px-6 py-16 text-ink">
      <section className="mx-auto grid max-w-6xl gap-10 rounded-lg border border-border bg-white p-8 shadow-soft md:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-sm font-bold text-primary">
            <ShieldCheck aria-hidden className="h-4 w-4" />
            Nền tảng quản lý bảo hiểm
          </p>
          <h1 className="mt-6 text-4xl font-extrabold leading-tight md:text-5xl">
            Vận hành bảo hiểm chuyên nghiệp cho quản trị, nhân viên và khách hàng
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted">
            Theo dõi hợp đồng, hồ sơ bồi thường, lịch hẹn, chat hỗ trợ và tài
            liệu tri thức doanh nghiệp trong một không gian bảo mật.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 text-sm font-bold text-white transition hover:bg-blue-700"
              href="/login"
            >
              Đăng nhập
              <ArrowRight aria-hidden className="h-4 w-4" />
            </Link>
            <Link
              className="rounded-md border border-border bg-white px-5 py-3 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
              href="/dashboard"
            >
              Vào bảng điều khiển
            </Link>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-mist p-5">
          <div className="grid gap-3">
            {["Hợp đồng đang hiệu lực", "Bồi thường chờ xử lý", "Lịch hẹn hôm nay"].map(
              (item, index) => (
                <div
                  className="rounded-lg border border-border bg-white p-4 shadow-sm"
                  key={item}
                >
                  <p className="text-sm font-bold text-muted">{item}</p>
                  <p className="mt-2 text-3xl font-extrabold text-ink">
                    {[128, 24, 9][index]}
                  </p>
                </div>
              ),
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
