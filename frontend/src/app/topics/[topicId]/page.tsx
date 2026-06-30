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
  if (rating === null) return <span className="text-zinc-400">No ratings</span>;
  return (
    <span className="text-zinc-600 dark:text-zinc-400">
      {"★".repeat(Math.round(rating))}
      {"☆".repeat(5 - Math.round(rating))}
      <span className="ml-1">{rating.toFixed(1)}</span>
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
          <div className="h-8 w-48 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
          <div className="h-4 w-96 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse mt-2" />
        </div>
      </main>
    );
  }

  if (topicError || !topic) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <p className="text-red-600 dark:text-red-400">Topic not found</p>
        <Link href="/" className="mt-4 text-zinc-600 dark:text-zinc-400 underline">
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
          className="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 mb-4 inline-block"
        >
          ← All Topics
        </Link>

        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          {topic.name}
        </h1>
        {topic.description && (
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">{topic.description}</p>
        )}

        <section className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {useRecs ? "Recommended Mentors" : "Mentors"}
            </h2>
            {!isAuthenticated && !authLoading && (
              <Link
                href="/auth/signin"
                className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                Sign in for personalized recommendations
              </Link>
            )}
          </div>

          {mentorLoading ? (
            <div className="grid gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"
                />
              ))}
            </div>
          ) : mentorError ? (
            <p className="text-red-600 dark:text-red-400">Failed to load mentors</p>
          ) : mentorData && mentorData.length > 0 ? (
            <div className="grid gap-4">
              {mentorData.map((mentor: RecommendedMentor | MentorBrief) => {
                const isRecommended = "score" in mentor;
                const recMentor = isRecommended ? (mentor as RecommendedMentor) : null;
                return (
                  <Link
                    key={mentor.id}
                    href={`/mentors/${mentor.user_id}`}
                    className="block p-4 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {recMentor && (
                          <p className="font-medium text-zinc-900 dark:text-zinc-100">
                            {recMentor.display_name || "Anonymous"}
                          </p>
                        )}
                        {mentor.headline && (
                          <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                            {mentor.headline}
                          </p>
                        )}
                        <div className="mt-2 text-sm">
                          <StarRating rating={mentor.rating_avg} />
                          <span className="ml-2 text-zinc-400">
                            ({mentor.rating_count} reviews)
                          </span>
                        </div>
                      </div>
                      {recMentor && (
                        <span className="text-xs px-2 py-1 bg-zinc-100 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded">
                          {Math.round(recMentor.score * 100)}% match
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <p className="text-zinc-500 dark:text-zinc-400 py-8 text-center">
              No mentors available for this topic yet
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
