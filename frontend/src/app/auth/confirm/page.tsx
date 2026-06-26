"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";

export default function ConfirmPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { confirmSignUp, resendCode } = useAuth();

  const emailParam = searchParams.get("email") ?? "";
  const [email, setEmail] = useState(emailParam);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      await confirmSignUp(email, code);
      router.push("/auth/signin");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Confirmation failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      setError("Please enter your email");
      return;
    }

    setError("");
    setMessage("");

    try {
      await resendCode(email);
      setMessage("A new verification code has been sent to your email");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to resend code";
      setError(msg);
    }
  };

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link
            href="/"
            className="text-xl font-bold text-zinc-900 dark:text-zinc-100"
          >
            SkillSwap
          </Link>
          <h1 className="mt-6 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            Check your email
          </h1>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            We sent a verification code to your email address
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="p-3 text-sm text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg">
              {error}
            </div>
          )}

          {message && (
            <div className="p-3 text-sm text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded-lg">
              {message}
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5"
            >
              Email address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 focus:border-transparent transition-shadow"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="code"
              className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5"
            >
              Verification code
            </label>
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              autoComplete="one-time-code"
              className="w-full px-3 py-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 focus:border-transparent transition-shadow"
              placeholder="Enter 6-digit code"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={handleResend}
            className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            Didn&apos;t receive a code? <span className="font-medium underline">Resend</span>
          </button>
        </div>

        <p className="mt-4 text-center text-sm text-zinc-600 dark:text-zinc-400">
          <Link
            href="/auth/signin"
            className="font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
          >
            Back to sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
