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
      className="block p-4 bg-white border-2 border-cream-dark rounded-lg hover:border-terracotta transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-ink">
            {otherParty?.display_name || otherParty?.email || "Unknown"}
          </p>
          <p className="text-sm text-ink-muted">{otherPartyLabel}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded ${statusClass}`}>
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
    <div className="p-4 bg-white border-2 border-cream-dark rounded-lg">
      <div className="flex items-center justify-between">
        <div>
          {meeting.scheduled_time && (
            <p className="font-medium text-ink">{formatDateTime(meeting.scheduled_time)}</p>
          )}
          {otherParty && (
            <p className="text-sm text-ink-muted">
              with {otherParty.display_name || otherParty.email}
            </p>
          )}
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded ${statusClass}`}>
          {meeting.status}
        </span>
      </div>
      {meeting.meeting_url && meeting.status === "SCHEDULED" && (
        <a
          href={meeting.meeting_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-3 text-sm font-medium text-terracotta hover:text-terracotta-dark"
        >
          Join Meeting →
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
      <header className="border-b border-cream-dark bg-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display text-xl font-bold text-ink">
            SkillSwap
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard/profile"
              className="text-sm text-ink-muted hover:text-ink transition-colors"
            >
              Profile
            </Link>
            <Link
              href="/dashboard/mentor-profile"
              className="text-sm text-ink-muted hover:text-ink transition-colors"
            >
              Mentor Profile
            </Link>
            <button
              onClick={handleSignOut}
              className="text-sm text-ink-muted hover:text-ink transition-colors"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>

      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display text-2xl text-ink">Dashboard</h1>
          {user && (
            <p className="text-sm text-ink-muted">
              Welcome, {user.display_name || user.email}
            </p>
          )}
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-8">
            <section>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="font-display text-lg text-ink">My Mentorships</h2>
                <div className="flex-1 h-px bg-cream-dark" />
              </div>

              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setActiveTab("mentee")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === "mentee"
                      ? "bg-terracotta text-white"
                      : "bg-cream-dark text-ink-muted hover:text-ink"
                  }`}
                >
                  As Mentee ({mentorshipsAsMentee.length})
                </button>
                <button
                  onClick={() => setActiveTab("mentor")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === "mentor"
                      ? "bg-terracotta text-white"
                      : "bg-cream-dark text-ink-muted hover:text-ink"
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
                <div className="space-y-3">
                  {activeMentorships.map((mentorship) => (
                    <MentorshipCard key={mentorship.id} mentorship={mentorship} role={activeTab} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 bg-white border-2 border-cream-dark rounded-lg">
                  <p className="text-ink-muted">
                    {activeTab === "mentee"
                      ? "You have no mentorships as a mentee yet."
                      : "You have no mentorships as a mentor yet."}
                  </p>
                  {activeTab === "mentee" && (
                    <Link
                      href="/"
                      className="inline-block mt-3 text-sm font-medium text-terracotta hover:text-terracotta-dark"
                    >
                      Browse topics to find a mentor →
                    </Link>
                  )}
                </div>
              )}
            </section>

            <section>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="font-display text-lg text-ink">Upcoming Meetings</h2>
                <div className="flex-1 h-px bg-cream-dark" />
              </div>

              {meetingsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i} className="h-20 bg-cream-dark rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : upcomingMeetings.length > 0 ? (
                <div className="space-y-3">
                  {upcomingMeetings.map((meeting) => (
                    <MeetingCard key={meeting.id} meeting={meeting} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 bg-white border-2 border-cream-dark rounded-lg">
                  <p className="text-ink-muted">No upcoming meetings</p>
                </div>
              )}
            </section>
          </div>

          <div>
            <section>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="font-display text-lg text-ink">Recommended</h2>
                <div className="flex-1 h-px bg-cream-dark" />
              </div>

              {recommendationsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-20 bg-cream-dark rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : recommendationsData && recommendationsData.items.length > 0 ? (
                <div className="space-y-3">
                  {recommendationsData.items.slice(0, 5).map((mentor) => (
                    <Link
                      key={mentor.id}
                      href={`/mentors/${mentor.user_id}`}
                      className="block p-4 bg-white border-2 border-cream-dark rounded-lg hover:border-olive transition-colors"
                    >
                      <p className="font-medium text-ink text-sm">
                        {mentor.display_name || "Anonymous"}
                      </p>
                      {mentor.headline && (
                        <p className="text-xs text-ink-muted mt-1 line-clamp-2">
                          {mentor.headline}
                        </p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-golden-dark">
                          {mentor.rating_avg != null
                            ? `★ ${Number(mentor.rating_avg).toFixed(1)}`
                            : "New mentor"}
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-olive-light text-olive-dark rounded">
                          {Math.round(mentor.score * 100)}% match
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 bg-white border-2 border-cream-dark rounded-lg">
                  <p className="text-ink-muted text-sm">No recommendations yet</p>
                  <Link
                    href="/"
                    className="inline-block mt-2 text-sm font-medium text-terracotta hover:text-terracotta-dark"
                  >
                    Browse topics →
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
