"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { useMentorProfile, useMentorReviews, useMentorTopics } from "@/hooks/use-mentors";
import { useCreateMentorship } from "@/hooks/use-mentorship";
import { ApiError } from "@/lib/api";

interface PageProps {
  params: Promise<{ userId: string }>;
}

const topicColors = [
  "bg-terracotta-light text-terracotta-dark hover:bg-terracotta hover:text-white",
  "bg-olive-light text-olive-dark hover:bg-olive hover:text-white",
  "bg-golden-light text-golden-dark hover:bg-golden hover:text-white",
  "bg-teal-light text-teal-dark hover:bg-teal hover:text-white",
];

function StarRating({ rating, size = "md" }: { rating: number | null; size?: "sm" | "md" }) {
  const textSize = size === "sm" ? "text-sm" : "text-lg";
  if (rating === null || rating === undefined) {
    return <span className={`text-ink-faint ${textSize}`}>No ratings yet</span>;
  }
  const numRating = Number(rating);
  if (isNaN(numRating)) {
    return <span className={`text-ink-faint ${textSize}`}>No ratings yet</span>;
  }
  return (
    <span className={`text-golden-dark ${textSize}`}>
      {"★".repeat(Math.round(numRating))}
      {"☆".repeat(5 - Math.round(numRating))}
      <span className="ml-1 text-ink-muted">{numRating.toFixed(1)}</span>
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

  const { data: topicsData, isLoading: topicsLoading } = useMentorTopics(userId);

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
          <div className="h-6 w-32 bg-cream-dark rounded animate-pulse" />
          <div className="h-8 w-64 bg-cream-dark rounded animate-pulse mt-4" />
          <div className="h-32 bg-cream-dark rounded-lg animate-pulse mt-4" />
        </div>
      </main>
    );
  }

  if (mentorError || !mentor) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <p className="text-error">Mentor not found</p>
        <Link href="/" className="mt-4 text-terracotta hover:text-terracotta-dark">
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
          className="text-sm font-bold text-ink-muted hover:text-terracotta mb-6 inline-block"
        >
          ← Browse Topics
        </Link>

        <div className="bg-white border-[3px] border-ink rounded-lg p-8">
          {mentor.headline && (
            <h1 className="font-display text-3xl text-ink">{mentor.headline}</h1>
          )}

          <div className="mt-4 flex items-center gap-3">
            <StarRating rating={mentor.rating_avg ? Number(mentor.rating_avg) : null} />
            <span className="text-ink-faint font-medium">({mentor.rating_count} reviews)</span>
          </div>

          {mentor.bio && (
            <div className="mt-8">
              <h2 className="text-sm font-bold uppercase tracking-wide text-ink-muted mb-3">About</h2>
              <p className="text-ink leading-relaxed whitespace-pre-wrap">{mentor.bio}</p>
            </div>
          )}

          <div className="mt-8">
            <h2 className="text-sm font-bold uppercase tracking-wide text-ink-muted mb-3">Topics</h2>
            {topicsLoading ? (
              <div className="flex gap-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-10 w-24 bg-cream-dark rounded-lg animate-pulse" />
                ))}
              </div>
            ) : topicsData && topicsData.topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topicsData.topics.map((topic, index) => (
                  <Link
                    key={topic.id}
                    href={`/topics/${topic.id}`}
                    className={`px-4 py-2 text-sm font-bold rounded-lg transition-colors ${topicColors[index % topicColors.length]}`}
                  >
                    {topic.name}
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-ink-faint font-medium">No topics listed</p>
            )}
          </div>

          <div className="mt-10 pt-8 border-t-[3px] border-cream-dark">
            {authLoading ? (
              <div className="h-12 w-48 bg-cream-dark rounded-lg animate-pulse" />
            ) : isAuthenticated ? (
              <div>
                <button
                  onClick={handleRequestMentorship}
                  disabled={createMentorship.isPending}
                  className="btn btn-primary"
                >
                  {createMentorship.isPending ? "Requesting..." : "Request Mentorship"}
                </button>
                {requestError && (
                  <p className="mt-3 text-sm font-medium text-error">{requestError}</p>
                )}
              </div>
            ) : (
              <Link href="/auth/signin" className="btn btn-primary">
                Sign in to request mentorship
              </Link>
            )}
          </div>
        </div>

        <section className="mt-12">
          <div className="flex items-center gap-4 mb-8">
            <h2 className="font-display text-2xl text-ink">Reviews</h2>
            <div className="flex-1 h-[3px] bg-ink" />
          </div>

          {reviewsLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-28 bg-cream-dark rounded-lg animate-pulse" />
              ))}
            </div>
          ) : reviewsError ? (
            <p className="text-error font-bold">Failed to load reviews</p>
          ) : reviewsData && reviewsData.reviews.length > 0 ? (
            <div className="space-y-4">
              {reviewsData.reviews.map((review) => (
                <div
                  key={review.id}
                  className="p-6 bg-white border-[3px] border-cream-dark rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <StarRating rating={review.rating} size="sm" />
                    <span className="text-sm font-medium text-ink-faint">{formatDate(review.created_at)}</span>
                  </div>
                  {review.comment && (
                    <p className="mt-4 text-ink leading-relaxed">{review.comment}</p>
                  )}
                  {review.reviewer && (
                    <p className="mt-4 text-sm font-bold text-ink-muted">
                      — {review.reviewer.display_name || review.reviewer.email}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10 bg-white border-[3px] border-cream-dark rounded-lg">
              <p className="text-ink-muted font-medium">No reviews yet</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
