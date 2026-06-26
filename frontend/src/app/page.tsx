"use client";

import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="text-center max-w-md">
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          SkillSwap
        </h1>
        <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-400 leading-relaxed">
          Connect with experienced mentors and grow your skills through
          personalized guidance.
        </p>

        <div className="mt-8">
          {isLoading ? (
            <p className="text-zinc-500">Loading...</p>
          ) : isAuthenticated ? (
            <Link
              href="/dashboard"
              className="inline-block px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
            >
              Go to Dashboard
            </Link>
          ) : (
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/auth/signin"
                className="px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                className="px-6 py-3 border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
              >
                Create Account
              </Link>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
