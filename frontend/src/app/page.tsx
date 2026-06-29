"use client";

import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";
import { useTopics } from "@/hooks/use-topics";

export default function Home() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: topicsData, isLoading: topicsLoading, error } = useTopics();

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="max-w-4xl mx-auto w-full">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            SkillSwap
          </h1>
          <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-400 leading-relaxed max-w-md mx-auto">
            Connect with experienced mentors and grow your skills through
            personalized guidance.
          </p>

          <div className="mt-8">
            {authLoading ? (
              <p className="text-zinc-500">Loading...</p>
            ) : isAuthenticated ? (
              <Link
                href="/dashboard"
                className="inline-block px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
              >
                Continue to Dashboard
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

        <section>
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100 mb-6">
            Browse Topics
          </h2>

          {topicsLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"
                />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600 dark:text-red-400">
                Failed to load topics
              </p>
            </div>
          ) : topicsData && topicsData.items.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {topicsData.items.map((topic) => (
                <Link
                  key={topic.id}
                  href={`/topics/${topic.id}`}
                  className="group p-4 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                >
                  <h3 className="font-medium text-zinc-900 dark:text-zinc-100 group-hover:text-zinc-700 dark:group-hover:text-zinc-200">
                    {topic.name}
                  </h3>
                  {topic.description && (
                    <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400 line-clamp-2">
                      {topic.description}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-zinc-500 dark:text-zinc-400">
                No topics available yet
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
