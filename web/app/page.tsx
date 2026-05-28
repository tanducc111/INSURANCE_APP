import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-mist px-6 py-8 text-ink">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl flex-col justify-between">
        <header className="flex items-center justify-between border-b border-slate-200 pb-5">
          <div>
            <p className="text-sm font-medium uppercase text-ocean">
              Operations
            </p>
            <h1 className="mt-2 text-3xl font-semibold">Insurance Management</h1>
          </div>
          <Link
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800"
            href="/login"
          >
            Sign in
          </Link>
        </header>

        <div className="grid gap-4 py-10 md:grid-cols-3">
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Admin</p>
            <p className="mt-2 text-2xl font-semibold">Company control</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Employee</p>
            <p className="mt-2 text-2xl font-semibold">Customer care</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Customer</p>
            <p className="mt-2 text-2xl font-semibold">Policy access</p>
          </div>
        </div>

        <footer className="flex flex-wrap items-center gap-3 border-t border-slate-200 pt-5">
          <Link
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-ink transition hover:border-ocean hover:text-ocean"
            href="/dashboard"
          >
            Open dashboard
          </Link>
        </footer>
      </section>
    </main>
  );
}
