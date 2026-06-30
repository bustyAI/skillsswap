"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { useMentorProfile, useMentorReviews } from "@/hooks/use-mentors";
import { useCreateMentorship } from "@/hooks/use-mentorship";
import { ApiError } from "@/lib/api";

interface PageProps {
  params: Promise<{ userId: string }>;
}

function StarRating({ rating, size = "md" }: { rating: number | null; size?: "sm" | "md" }) {
  const textSize = size === "sm" ? "text-sm" : "text-lg";
  if (rating === null) {
    return <span className={`text-zinc-400 ${textSize}`}>No ratings yet</span>;
  }
  return (
    <span className={`text-zinc-600 dark:text-zinc-400 ${textSize}`}>
      {"★".repeat(Math.round(rating))}
      {"☆".repeat(5 - Math.round(rating))}
      <span className="ml-1">{rating.toFixed(1)}</span>
    </span>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function MentorPage({ params }: PageProps) {
  const { userId } = use(params);
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [requestError, setRequestError] = useState<string | null>(null);

  const {
    data: mentor,
    isLoading: mentorLoading,
    error: mentorError,
  } = useMentorProfile(userId);

  const {
    data: reviewsData,
    isLoading: reviewsLoading,
    error: reviewsError,
  } = useMentorReviews(userId);

  const createMentorship = useCreateMentorship();

  const handleRequestMentorship = async () => {
    if (!mentor) return;
    setRequestError(null);

    try {
      await createMentorship.mutateAsync({ mentorId: userId });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setRequestError("You already have a mentorship with this mentor");
        } else if (err.status === 400) {
          setRequestError(err.message);
        } else {
          setRequestError("Failed to request mentorship");
        }
      } else {
        setRequestError("An unexpected error occurred");
      }
    }
  };

  if (mentorLoading) {
    return (
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="max-w-3xl mx-auto w-full">
          <div className="h-6 w-32 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
          <div className="h-8 w-64 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse mt-4" />
          <div className="h-24 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse mt-4" />
        </div>
      </main>
    );
  }

  if (mentorError || !mentor) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <p className="text-red-600 dark:text-red-400">Mentor not found</p>
        <Link href="/" className="mt-4 text-zinc-600 dark:text-zinc-400 underline">
          Browse topics
        </Link>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="max-w-3xl mx-auto w-full">
        <Link
          href="/"
          className="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 mb-6 inline-block"
        >
          ← Browse Topics
        </Link>

        <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-6">
          {mentor.headline && (
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              {mentor.headline}
            </h1>
          )}

          <div className="mt-3 flex items-center gap-4">
            <StarRating rating={mentor.rating_avg ? Number(mentor.rating_avg) : null} />
            <span className="text-zinc-400">({mentor.rating_count} reviews)</span>
          </div>

          {mentor.bio && (
            <div className="mt-6">
              <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
                About
              </h2>
              <p className="mt-2 text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">
                {mentor.bio}
              </p>
            </div>
          )}

          <div className="mt-6 pt-6 border-t border-zinc-200 dark:border-zinc-700">
            {authLoading ? (
              <div className="h-10 w-40 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
            ) : isAuthenticated ? (
              <div>
                <button
                  onClick={handleRequestMentorship}
                  disabled={createMentorship.isPending}
                  className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMentorship.isPending ? "Requesting..." : "Request Mentorship"}
                </button>
                {requestError && (
                  <p className="mt-2 text-sm text-red-600 dark:text-red-400">{requestError}</p>
                )}
              </div>
            ) : (
              <Link
                href="/auth/signin"
                className="inline-block px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
              >
                Sign in to request mentorship
              </Link>
            )}
          </div>
        </div>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
            Reviews
          </h2>

          {reviewsLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-20 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse"
                />
              ))}
            </div>
          ) : reviewsError ? (
            <p className="text-red-600 dark:text-red-400">Failed to load reviews</p>
          ) : reviewsData && reviewsData.reviews.length > 0 ? (
            <div className="space-y-4">
              {reviewsData.reviews.map((review) => (
                <div
                  key={review.id}
                  className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StarRating rating={review.rating} size="sm" />
                    </div>
                    <span className="text-sm text-zinc-400">
                      {formatDate(review.created_at)}
                    </span>
                  </div>
                  {review.comment && (
                    <p className="mt-2 text-zinc-700 dark:text-zinc-300">{review.comment}</p>
                  )}
                  {review.reviewer && (
                    <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                      — {review.reviewer.display_name || review.reviewer.email}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500 dark:text-zinc-400 py-4">No reviews yet</p>
          )}
        </section>
      </div>
    </main>
  );
}
