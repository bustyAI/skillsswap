"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { useUser } from "@/hooks/use-user";
import { useMyMentorships } from "@/hooks/use-mentorship";
import { useMyMeetings } from "@/hooks/use-meetings";
import { useTopics } from "@/hooks/use-topics";
import { useRecommendations } from "@/hooks/use-mentors";
import type { Mentorship, Meeting } from "@/lib/types";

type MentorshipTab = "mentee" | "mentor";

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function MentorshipCard({ mentorship, role }: { mentorship: Mentorship; role: MentorshipTab }) {
  const otherParty = role === "mentee" ? mentorship.mentor : mentorship.mentee;
  const otherPartyLabel = role === "mentee" ? "Mentor" : "Mentee";

  return (
    <Link
      href={`/mentorships/${mentorship.id}`}
      className="block p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-zinc-900 dark:text-zinc-100">
            {otherParty?.display_name || otherParty?.email || "Unknown"}
          </p>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {otherPartyLabel}
          </p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded ${
            mentorship.status === "ACTIVE"
              ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
              : mentorship.status === "REQUESTED"
              ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400"
              : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
          }`}
        >
          {mentorship.status}
        </span>
      </div>
    </Link>
  );
}

function MeetingCard({ meeting }: { meeting: Meeting }) {
  const otherParty =
    meeting.mentorship?.mentor || meeting.mentorship?.mentee;

  return (
    <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg">
      <div className="flex items-center justify-between">
        <div>
          {meeting.scheduled_time && (
            <p className="font-medium text-zinc-900 dark:text-zinc-100">
              {formatDateTime(meeting.scheduled_time)}
            </p>
          )}
          {otherParty && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              with {otherParty.display_name || otherParty.email}
            </p>
          )}
        </div>
        <span
          className={`text-xs px-2 py-1 rounded ${
            meeting.status === "SCHEDULED"
              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
              : meeting.status === "REQUESTED"
              ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400"
              : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
          }`}
        >
          {meeting.status}
        </span>
      </div>
      {meeting.meeting_url && meeting.status === "SCHEDULED" && (
        <a
          href={meeting.meeting_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-2 text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
        >
          Join Meeting
        </a>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { signOut } = useAuth();
  const { user, isLoading: userLoading } = useUser();
  const { data: mentorshipsData, isLoading: mentorshipsLoading } = useMyMentorships();
  const { data: meetingsData, isLoading: meetingsLoading } = useMyMeetings();
  const { data: topicsData } = useTopics(1, 1);
  const [activeTab, setActiveTab] = useState<MentorshipTab>("mentee");

  const defaultTopicId = topicsData?.items[0]?.id;
  const { data: recommendationsData, isLoading: recommendationsLoading } = useRecommendations(
    defaultTopicId,
    !!defaultTopicId
  );

  const handleSignOut = () => {
    signOut();
    router.push("/");
  };

  const mentorshipsAsMentee = mentorshipsData?.items.filter(
    (m) => m.mentee_id === user?.id
  ) ?? [];

  const mentorshipsAsMentor = mentorshipsData?.items.filter(
    (m) => m.mentor_id === user?.id
  ) ?? [];

  const activeMentorships = activeTab === "mentee" ? mentorshipsAsMentee : mentorshipsAsMentor;

  const upcomingMeetings = meetingsData?.items.filter(
    (m) => m.status === "SCHEDULED" || m.status === "REQUESTED"
  ) ?? [];

  if (userLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
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
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard/profile"
              className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Edit Profile
            </Link>
            <Link
              href="/dashboard/mentor-profile"
              className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Mentor Profile
            </Link>
            <button
              onClick={handleSignOut}
              className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            Dashboard
          </h1>
          {user && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {user.display_name || user.email}
            </p>
          )}
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-8">
            <section>
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4">
                My Mentorships
              </h2>

              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setActiveTab("mentee")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === "mentee"
                      ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  As Mentee ({mentorshipsAsMentee.length})
                </button>
                <button
                  onClick={() => setActiveTab("mentor")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === "mentor"
                      ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  As Mentor ({mentorshipsAsMentor.length})
                </button>
              </div>

              {mentorshipsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse"
                    />
                  ))}
                </div>
              ) : activeMentorships.length > 0 ? (
                <div className="space-y-3">
                  {activeMentorships.map((mentorship) => (
                    <MentorshipCard
                      key={mentorship.id}
                      mentorship={mentorship}
                      role={activeTab}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border border-zinc-200 dark:border-zinc-700 rounded-lg">
                  <p className="text-zinc-500 dark:text-zinc-400">
                    {activeTab === "mentee"
                      ? "You have no mentorships as a mentee yet."
                      : "You have no mentorships as a mentor yet."}
                  </p>
                  {activeTab === "mentee" && (
                    <Link
                      href="/"
                      className="inline-block mt-4 text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
                    >
                      Browse topics to find a mentor
                    </Link>
                  )}
                </div>
              )}
            </section>

            <section>
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4">
                Upcoming Meetings
              </h2>

              {meetingsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-20 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse"
                    />
                  ))}
                </div>
              ) : upcomingMeetings.length > 0 ? (
                <div className="space-y-3">
                  {upcomingMeetings.map((meeting) => (
                    <MeetingCard key={meeting.id} meeting={meeting} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border border-zinc-200 dark:border-zinc-700 rounded-lg">
                  <p className="text-zinc-500 dark:text-zinc-400">
                    No upcoming meetings
                  </p>
                </div>
              )}
            </section>
          </div>

          <div>
            <section>
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4">
                Recommended Mentors
              </h2>

              {recommendationsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse"
                    />
                  ))}
                </div>
              ) : recommendationsData && recommendationsData.items.length > 0 ? (
                <div className="space-y-3">
                  {recommendationsData.items.slice(0, 5).map((mentor) => (
                    <Link
                      key={mentor.id}
                      href={`/mentors/${mentor.user_id}`}
                      className="block p-3 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                    >
                      <p className="font-medium text-zinc-900 dark:text-zinc-100 text-sm">
                        {mentor.display_name || "Anonymous"}
                      </p>
                      {mentor.headline && (
                        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-1">
                          {mentor.headline}
                        </p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-zinc-400">
                          {mentor.rating_avg
                            ? `★ ${mentor.rating_avg.toFixed(1)}`
                            : "No ratings"}
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-zinc-100 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded">
                          {Math.round(mentor.score * 100)}% match
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border border-zinc-200 dark:border-zinc-700 rounded-lg">
                  <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                    No recommendations available
                  </p>
                  <Link
                    href="/"
                    className="inline-block mt-2 text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
                  >
                    Browse topics
                  </Link>
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
