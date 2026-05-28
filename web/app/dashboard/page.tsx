export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">
          Dashboard
        </p>
        <h1 className="mt-2 text-3xl font-semibold">Overview</h1>
      </header>

      <div className="mt-6 rounded-md border border-dashed border-slate-300 bg-white p-6">
        <p className="text-sm font-medium text-slate-500">
          No dashboard data available.
        </p>
      </div>
    </div>
  );
}
