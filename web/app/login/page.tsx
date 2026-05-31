"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

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
        setError("Unable to sign in");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist px-6 py-10 text-ink">
      <section className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-sm font-medium uppercase text-ocean">
            Secure access
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Sign in</h1>
        </div>

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none transition focus:border-ocean focus:ring-2 focus:ring-teal-100"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@company.com"
              required
              type="email"
              value={email}
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none transition focus:border-ocean focus:ring-2 focus:ring-teal-100"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              required
              type="password"
              value={password}
            />
          </label>

          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700">
              {error}
            </p>
          ) : null}

          <button
            className="w-full rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
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
