"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { useUser } from "@/hooks/use-user";

export default function DashboardPage() {
  const router = useRouter();
  const { signOut } = useAuth();
  const { user, isLoading, error } = useUser();

  const handleSignOut = () => {
    signOut();
    router.push("/");
  };

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">
            Failed to load user data
          </p>
          <button
            onClick={handleSignOut}
            className="text-sm text-zinc-600 dark:text-zinc-400 hover:underline"
          >
            Sign out and try again
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="text-xl font-bold text-zinc-900 dark:text-zinc-100"
          >
            SkillSwap
          </Link>
          <button
            onClick={handleSignOut}
            className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100 mb-8">
          Dashboard
        </h1>

        <section className="bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-6">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4">
            Your Profile
          </h2>

          {user ? (
            <dl className="space-y-4">
              <div>
                <dt className="text-sm text-zinc-500 dark:text-zinc-400">
                  Email
                </dt>
                <dd className="mt-1 text-zinc-900 dark:text-zinc-100">
                  {user.email}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-zinc-500 dark:text-zinc-400">
                  Display Name
                </dt>
                <dd className="mt-1 text-zinc-900 dark:text-zinc-100">
                  {user.display_name || (
                    <span className="text-zinc-400 dark:text-zinc-500 italic">
                      Not set
                    </span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-zinc-500 dark:text-zinc-400">
                  Member Since
                </dt>
                <dd className="mt-1 text-zinc-900 dark:text-zinc-100">
                  {new Date(user.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-zinc-500">No profile data available</p>
          )}
        </section>
      </div>
    </main>
  );
}
