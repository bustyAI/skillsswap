"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { useUser, useUpdateUser } from "@/hooks/use-user";
import { ApiError } from "@/lib/api";

const profileSchema = z.object({
  display_name: z
    .string()
    .min(2, "Display name must be at least 2 characters")
    .max(100, "Display name must be less than 100 characters")
    .nullable()
    .transform((val) => val?.trim() || null),
});

function ProfileForm({ initialDisplayName }: { initialDisplayName: string | null }) {
  const router = useRouter();
  const updateUser = useUpdateUser();

  const [displayName, setDisplayName] = useState(initialDisplayName || "");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setApiError(null);
    setSuccess(false);

    const result = profileSchema.safeParse({
      display_name: displayName || null,
    });
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        if (issue.path[0]) {
          fieldErrors[issue.path[0] as string] = issue.message;
        }
      }
      setErrors(fieldErrors);
      return;
    }

    try {
      await updateUser.mutateAsync(result.data);
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err.message);
      } else {
        setApiError("An unexpected error occurred");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="display_name" className="block text-sm font-medium text-ink mb-2">
          Display Name
        </label>
        <input
          type="text"
          id="display_name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Enter your display name"
          className={`input ${errors.display_name ? "border-error" : ""}`}
        />
        {errors.display_name && (
          <p className="mt-1 text-sm text-error">{errors.display_name}</p>
        )}
      </div>

      {apiError && (
        <div className="p-4 bg-error-light rounded-lg">
          <p className="text-sm text-error">{apiError}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-success-light rounded-lg">
          <p className="text-sm text-success">Profile updated successfully</p>
        </div>
      )}

      <div className="flex items-center gap-4">
        <button type="submit" disabled={updateUser.isPending} className="btn btn-primary">
          {updateUser.isPending ? "Saving..." : "Save Changes"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="btn btn-secondary"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function ProfilePage() {
  const { user, isLoading } = useUser();

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-ink-muted">Loading...</p>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b border-cream-dark bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display text-xl font-bold text-ink">
            SkillSwap
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-ink-muted hover:text-ink transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </header>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-8">
        <h1 className="font-display text-2xl text-ink mb-8">Edit Profile</h1>

        <div className="mb-6">
          <label className="block text-sm font-medium text-ink mb-2">Email</label>
          <input
            type="email"
            value={user?.email || ""}
            disabled
            className="input bg-cream-dark text-ink-muted cursor-not-allowed"
          />
          <p className="mt-1 text-xs text-ink-faint">Email cannot be changed</p>
        </div>

        {user && <ProfileForm key={user.id} initialDisplayName={user.display_name} />}
      </div>
    </main>
  );
}
