"use client";

import { use } from "react";
import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";
import { useTopic } from "@/hooks/use-topics";
import { useRecommendations, useTopicMentors } from "@/hooks/use-mentors";
import type { RecommendedMentor, MentorBrief } from "@/lib/types";

interface PageProps {
  params: Promise<{ topicId: string }>;
}

function StarRating({ rating }: { rating: number | null }) {
  if (rating === null || rating === undefined) return <span className="text-ink-faint">No ratings</span>;
  const numRating = Number(rating);
  if (isNaN(numRating)) return <span className="text-ink-faint">No ratings</span>;
  return (
    <span className="text-golden-dark">
      {"★".repeat(Math.round(numRating))}
      {"☆".repeat(5 - Math.round(numRating))}
      <span className="ml-1 text-ink-muted">{numRating.toFixed(1)}</span>
    </span>
  );
}

export default function TopicPage({ params }: PageProps) {
  const { topicId } = use(params);
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const { data: topic, isLoading: topicLoading, error: topicError } = useTopic(topicId);

  const {
    data: recommendations,
    isLoading: recsLoading,
    error: recsError,
  } = useRecommendations(topicId, isAuthenticated && !authLoading);

  const {
    data: topicMentors,
    isLoading: mentorsLoading,
    error: mentorsError,
  } = useTopicMentors(topicId);

  const useRecs = isAuthenticated && !authLoading;
  const mentorData = useRecs ? recommendations?.items : topicMentors?.items;
  const mentorLoading = useRecs ? recsLoading : mentorsLoading;
  const mentorError = useRecs ? recsError : mentorsError;

  if (topicLoading) {
    return (
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="max-w-4xl mx-auto w-full">
          <div className="h-8 w-48 bg-cream-dark rounded animate-pulse" />
          <div className="h-4 w-96 bg-cream-dark rounded animate-pulse mt-2" />
        </div>
      </main>
    );
  }

  if (topicError || !topic) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <p className="text-error">Topic not found</p>
        <Link href="/" className="mt-4 text-terracotta hover:text-terracotta-dark">
          Back to topics
        </Link>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="max-w-4xl mx-auto w-full">
        <Link
          href="/"
          className="text-sm font-bold text-ink-muted hover:text-terracotta mb-6 inline-block"
        >
          ← All Topics
        </Link>

        <h1 className="font-display text-4xl text-ink">{topic.name}</h1>
        {topic.description && (
          <p className="mt-3 text-ink-muted text-lg leading-relaxed">{topic.description}</p>
        )}

        <section className="mt-12">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <h2 className="font-display text-2xl text-ink">
                {useRecs ? "Recommended Mentors" : "Mentors"}
              </h2>
              <div className="flex-1 h-[3px] bg-ink min-w-[2rem]" />
            </div>
            {!isAuthenticated && !authLoading && (
              <Link
                href="/auth/signin"
                className="text-sm font-bold text-terracotta hover:text-terracotta-dark"
              >
                Sign in for recommendations
              </Link>
            )}
          </div>

          {mentorLoading ? (
            <div className="grid gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-28 rounded-lg bg-cream-dark animate-pulse" />
              ))}
            </div>
          ) : mentorError ? (
            <p className="text-error">Failed to load mentors</p>
          ) : mentorData && mentorData.length > 0 ? (
            <div className="grid gap-5">
              {mentorData.map((mentor: RecommendedMentor | MentorBrief) => {
                const isRecommended = "score" in mentor;
                const recMentor = isRecommended ? (mentor as RecommendedMentor) : null;
                return (
                  <Link
                    key={mentor.id}
                    href={`/mentors/${mentor.user_id}`}
                    className="block p-6 bg-white border-[3px] border-cream-dark rounded-lg hover:border-ink transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-lg text-ink">
                          {mentor.display_name || "Anonymous"}
                        </p>
                        {mentor.headline && (
                          <p className="text-ink-muted mt-1 font-medium">{mentor.headline}</p>
                        )}
                        {mentor.bio && (
                          <p className="text-ink-faint mt-2 line-clamp-2">{mentor.bio}</p>
                        )}
                        <div className="mt-4 flex items-center gap-3 text-sm">
                          <StarRating rating={mentor.rating_avg} />
                          <span className="text-ink-faint font-medium">({mentor.rating_count} reviews)</span>
                        </div>
                      </div>
                      {recMentor && (
                        <span className="text-xs font-bold uppercase tracking-wide px-3 py-1.5 bg-olive text-white rounded">
                          {Math.round(recMentor.score * 100)}% match
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 bg-white border-[3px] border-cream-dark rounded-lg">
              <p className="text-ink-muted font-medium">No mentors available for this topic yet</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
