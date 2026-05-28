import Link from "next/link";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="min-h-screen bg-mist text-ink">
      <div className="grid min-h-screen md:grid-cols-[240px_1fr]">
        <aside className="border-r border-slate-200 bg-white p-5">
          <Link className="text-lg font-semibold" href="/">
            Insurance Management
          </Link>
          <nav className="mt-8 space-y-2 text-sm font-medium text-slate-600">
            <Link
              className="block rounded-md px-3 py-2 hover:bg-slate-100 hover:text-ink"
              href="/dashboard"
            >
              Overview
            </Link>
          </nav>
        </aside>
        <section className="p-6 md:p-8">{children}</section>
      </div>
    </main>
  );
}
