"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";

function ConfirmForm() {
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
    <div className="w-full max-w-sm">
      <div className="text-center mb-8">
        <Link href="/" className="inline-block">
          <span className="font-display text-2xl font-bold text-ink">SkillSwap</span>
        </Link>
        <h1 className="mt-8 font-display text-2xl text-ink">Check your email</h1>
        <p className="mt-2 text-ink-muted">We sent a verification code to your email</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="p-3 text-sm text-error bg-error-light rounded-lg">
            {error}
          </div>
        )}

        {message && (
          <div className="p-3 text-sm text-success bg-success-light rounded-lg">
            {message}
          </div>
        )}

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-ink mb-1.5">
            Email address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="input"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="code" className="block text-sm font-medium text-ink mb-1.5">
            Verification code
          </label>
          <input
            id="code"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            autoComplete="one-time-code"
            className="input"
            placeholder="Enter 6-digit code"
          />
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full">
          {loading ? "Verifying..." : "Verify Email"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          onClick={handleResend}
          className="text-sm text-ink-muted hover:text-ink transition-colors"
        >
          Didn&apos;t receive a code?{" "}
          <span className="font-medium text-terracotta hover:text-terracotta-dark">Resend</span>
        </button>
      </div>

      <p className="mt-4 text-center text-sm text-ink-muted">
        <Link href="/auth/signin" className="font-medium text-terracotta hover:text-terracotta-dark">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

function ConfirmFormFallback() {
  return (
    <div className="w-full max-w-sm animate-pulse">
      <div className="text-center mb-8">
        <div className="h-6 w-24 bg-cream-dark rounded mx-auto" />
        <div className="mt-8 h-8 w-48 bg-cream-dark rounded mx-auto" />
        <div className="mt-2 h-4 w-64 bg-cream-dark rounded mx-auto" />
      </div>
      <div className="space-y-5">
        <div className="h-12 bg-cream-dark rounded-lg" />
        <div className="h-12 bg-cream-dark rounded-lg" />
        <div className="h-12 bg-cream-dark rounded-lg" />
      </div>
    </div>
  );
}

export default function ConfirmPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-12">
      <Suspense fallback={<ConfirmFormFallback />}>
        <ConfirmForm />
      </Suspense>
    </main>
  );
}
