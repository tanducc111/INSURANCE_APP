import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-mist px-6 py-10 text-ink">
      <section className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-sm font-medium uppercase text-ocean">
            Secure access
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Sign in</h1>
        </div>

        <form className="mt-8 space-y-5">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none transition focus:border-ocean focus:ring-2 focus:ring-teal-100"
              name="email"
              placeholder="name@company.com"
              type="email"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none transition focus:border-ocean focus:ring-2 focus:ring-teal-100"
              name="password"
              placeholder="Password"
              type="password"
            />
          </label>

          <button
            className="w-full rounded-md bg-slate-300 px-4 py-2 text-sm font-semibold text-slate-600"
            disabled
            type="button"
          >
            Sign in
          </button>
        </form>

        <Link
          className="mt-6 inline-flex text-sm font-semibold text-ocean hover:text-teal-800"
          href="/"
        >
          Back home
        </Link>
      </section>
    </main>
  );
}
