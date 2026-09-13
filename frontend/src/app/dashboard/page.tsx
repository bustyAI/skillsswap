"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
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

const statusColors = {
  ACTIVE: "bg-olive-light text-olive-dark",
  REQUESTED: "bg-golden-light text-golden-dark",
  SCHEDULED: "bg-teal-light text-teal-dark",
  DEFAULT: "bg-cream-dark text-ink-muted",
};

function MentorshipCard({ mentorship, role }: { mentorship: Mentorship; role: MentorshipTab }) {
  const otherParty = role === "mentee" ? mentorship.mentor : mentorship.mentee;
  const otherPartyLabel = role === "mentee" ? "Mentor" : "Mentee";
  const statusClass = statusColors[mentorship.status as keyof typeof statusColors] || statusColors.DEFAULT;

  return (
    <Link
      href={`/mentorships/${mentorship.id}`}
      className="block p-5 bg-white border-[3px] border-cream-dark rounded-lg hover:border-ink transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-bold text-ink">
            {otherParty?.display_name || otherParty?.email || "Unknown"}
          </p>
          <p className="text-sm text-ink-muted font-medium">{otherPartyLabel}</p>
        </div>
        <span className={`text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded ${statusClass}`}>
          {mentorship.status}
        </span>
      </div>
    </Link>
  );
}

function MeetingCard({ meeting }: { meeting: Meeting }) {
  const otherParty = meeting.mentorship?.mentor || meeting.mentorship?.mentee;
  const statusClass = statusColors[meeting.status as keyof typeof statusColors] || statusColors.DEFAULT;

  return (
    <div className="p-5 bg-white border-[3px] border-cream-dark rounded-lg">
      <div className="flex items-center justify-between">
        <div>
          {meeting.scheduled_time && (
            <p className="font-bold text-ink">{formatDateTime(meeting.scheduled_time)}</p>
          )}
          {otherParty && (
            <p className="text-sm text-ink-muted font-medium">
              with {otherParty.display_name || otherParty.email}
            </p>
          )}
        </div>
        <span className={`text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded ${statusClass}`}>
          {meeting.status}
        </span>
      </div>
      {meeting.meeting_url && meeting.status === "SCHEDULED" && (
        <a
          href={meeting.meeting_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-4 px-4 py-2 text-sm font-bold uppercase tracking-wide bg-teal text-white rounded hover:bg-teal-dark transition-colors"
        >
          Join Meeting
        </a>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
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
    queryClient.clear();
    signOut();
    router.push("/");
  };

  const mentorshipsAsMentee = mentorshipsData?.mentorships?.filter(
    (m) => m.mentee_id === user?.id
  ) ?? [];

  const mentorshipsAsMentor = mentorshipsData?.mentorships?.filter(
    (m) => m.mentor_id === user?.id
  ) ?? [];

  const activeMentorships = activeTab === "mentee" ? mentorshipsAsMentee : mentorshipsAsMentor;

  const upcomingMeetings = meetingsData?.meetings?.filter(
    (m) => m.status === "SCHEDULED" || m.status === "REQUESTED"
  ) ?? [];

  if (userLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-ink-muted">Loading...</p>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b-[3px] border-ink bg-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display text-xl font-bold text-ink">
            SkillSwap
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard/profile"
              className="text-sm font-semibold text-ink-muted hover:text-terracotta transition-colors"
            >
              Profile
            </Link>
            <Link
              href="/dashboard/mentor-profile"
              className="text-sm font-semibold text-ink-muted hover:text-terracotta transition-colors"
            >
              Mentor Profile
            </Link>
            <button
              onClick={handleSignOut}
              className="text-sm font-semibold text-ink-muted hover:text-terracotta transition-colors"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>

      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-10">
          <h1 className="font-display text-3xl text-ink">Dashboard</h1>
          {user && (
            <p className="text-sm font-medium text-ink-muted truncate">
              Welcome, <span className="text-ink font-bold">{user.display_name || user.email}</span>
            </p>
          )}
        </div>

        <div className="grid gap-10 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-10">
            <section>
              <div className="flex items-center gap-4 mb-6">
                <h2 className="font-display text-xl text-ink">My Mentorships</h2>
                <div className="flex-1 h-[3px] bg-ink" />
              </div>

              <div className="flex gap-2 mb-5">
                <button
                  onClick={() => setActiveTab("mentee")}
                  className={`px-5 py-2.5 text-sm font-bold uppercase tracking-wide rounded-lg transition-colors ${
                    activeTab === "mentee"
                      ? "bg-terracotta text-white shadow-[0_2px_0_var(--terracotta-dark)]"
                      : "bg-cream-dark text-ink-muted hover:text-ink border-[3px] border-transparent"
                  }`}
                >
                  As Mentee ({mentorshipsAsMentee.length})
                </button>
                <button
                  onClick={() => setActiveTab("mentor")}
                  className={`px-5 py-2.5 text-sm font-bold uppercase tracking-wide rounded-lg transition-colors ${
                    activeTab === "mentor"
                      ? "bg-terracotta text-white shadow-[0_2px_0_var(--terracotta-dark)]"
                      : "bg-cream-dark text-ink-muted hover:text-ink border-[3px] border-transparent"
                  }`}
                >
                  As Mentor ({mentorshipsAsMentor.length})
                </button>
              </div>

              {mentorshipsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-16 bg-cream-dark rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : activeMentorships.length > 0 ? (
                <div className="space-y-4">
                  {activeMentorships.map((mentorship) => (
                    <MentorshipCard key={mentorship.id} mentorship={mentorship} role={activeTab} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 bg-white border-[3px] border-cream-dark rounded-lg">
                  <p className="text-ink-muted font-medium">
                    {activeTab === "mentee"
                      ? "You have no mentorships as a mentee yet."
                      : "You have no mentorships as a mentor yet."}
                  </p>
                  {activeTab === "mentee" && (
                    <Link
                      href="/"
                      className="inline-block mt-4 px-5 py-2 text-sm font-bold uppercase tracking-wide bg-terracotta text-white rounded hover:bg-terracotta-dark transition-colors"
                    >
                      Find a Mentor
                    </Link>
                  )}
                </div>
              )}
            </section>

            <section>
              <div className="flex items-center gap-4 mb-6">
                <h2 className="font-display text-xl text-ink">Upcoming Meetings</h2>
                <div className="flex-1 h-[3px] bg-ink" />
              </div>

              {meetingsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i} className="h-24 bg-cream-dark rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : upcomingMeetings.length > 0 ? (
                <div className="space-y-4">
                  {upcomingMeetings.map((meeting) => (
                    <MeetingCard key={meeting.id} meeting={meeting} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 bg-white border-[3px] border-cream-dark rounded-lg">
                  <p className="text-ink-muted font-medium">No upcoming meetings</p>
                </div>
              )}
            </section>
          </div>

          <div className="min-w-0">
            <section className="bg-golden-light p-4 rounded-lg border-[3px] border-golden">
              <h2 className="font-display text-sm text-golden-dark text-center mb-3">Recommended</h2>

              {recommendationsLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-20 bg-white/50 rounded animate-pulse" />
                  ))}
                </div>
              ) : recommendationsData && recommendationsData.items.length > 0 ? (
                <div className="space-y-2">
                  {recommendationsData.items.slice(0, 5).map((mentor) => (
                    <Link
                      key={mentor.id}
                      href={`/mentors/${mentor.user_id}`}
                      className="block p-3 bg-white border-2 border-golden/30 rounded hover:border-golden-dark transition-colors"
                    >
                      <p className="font-bold text-ink text-xs truncate">
                        {mentor.display_name || "Anonymous"}
                      </p>
                      {mentor.headline && (
                        <p className="text-xs text-ink-muted mt-1 line-clamp-1">
                          {mentor.headline}
                        </p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs font-bold text-golden-dark">
                          {mentor.rating_avg != null
                            ? `★ ${Number(mentor.rating_avg).toFixed(1)}`
                            : "New"}
                        </span>
                        <span className="text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 bg-olive text-white rounded">
                          {Math.round(mentor.score * 100)}%
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 bg-white rounded border-2 border-golden/30">
                  <p className="text-ink-muted text-xs font-medium">No recommendations yet</p>
                  <Link
                    href="/"
                    className="inline-block mt-2 px-3 py-1.5 text-xs font-bold uppercase tracking-wide bg-golden text-white rounded hover:bg-golden-dark transition-colors"
                  >
                    Browse Topics
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
