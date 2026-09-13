"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import { useUser } from "@/hooks/use-user";
import { useMentorship, useAcceptMentorship, useEndMentorship } from "@/hooks/use-mentorship";
import { useMessages, useSendMessage } from "@/hooks/use-messages";
import {
  useMentorshipMeetings,
  useRequestMeeting,
  useScheduleMeeting,
} from "@/hooks/use-meetings";
import { ApiError } from "@/lib/api";
import type { Message, Meeting } from "@/lib/types";

const ALLOWED_MEETING_DOMAINS = [
  "zoom.us",
  "meet.google.com",
  "teams.microsoft.com",
  "whereby.com",
];

function isValidMeetingUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") return false;
    const hostname = parsed.hostname.toLowerCase();
    return ALLOWED_MEETING_DOMAINS.some(
      (domain) => hostname === domain || hostname.endsWith(`.${domain}`)
    );
  } catch {
    return false;
  }
}

const messageSchema = z.object({
  body: z.string().min(1, "Message cannot be empty").max(2000, "Message too long"),
});

const scheduleMeetingSchema = z.object({
  scheduled_time: z.string().min(1, "Please select a date and time"),
  meeting_url: z
    .string()
    .min(1, "Meeting URL is required")
    .refine(isValidMeetingUrl, {
      message: "URL must be HTTPS from Zoom, Google Meet, Teams, or Whereby",
    }),
});

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const statusStyles = {
  ACTIVE: "bg-olive-light text-olive-dark",
  REQUESTED: "bg-golden-light text-golden-dark",
  SCHEDULED: "bg-teal-light text-teal-dark",
  COMPLETED: "bg-olive-light text-olive-dark",
  CANCELLED: "bg-cream-dark text-ink-muted",
  ENDED: "bg-cream-dark text-ink-muted",
  DECLINED: "bg-error-light text-error",
};

function MeetingStatusBadge({ status }: { status: Meeting["status"] }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusStyles[status] || statusStyles.CANCELLED}`}>
      {status}
    </span>
  );
}

function ScheduleMeetingForm({
  meeting,
  onCancel,
}: {
  meeting: Meeting;
  onCancel: () => void;
}) {
  const scheduleMeeting = useScheduleMeeting();
  const [scheduledTime, setScheduledTime] = useState("");
  const [meetingUrl, setMeetingUrl] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setApiError(null);

    const result = scheduleMeetingSchema.safeParse({
      scheduled_time: scheduledTime,
      meeting_url: meetingUrl,
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
      await scheduleMeeting.mutateAsync({
        meetingId: meeting.id,
        data: {
          scheduled_time: new Date(result.data.scheduled_time).toISOString(),
          meeting_url: result.data.meeting_url,
        },
      });
      onCancel();
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err.message);
      } else {
        setApiError("Failed to schedule meeting");
      }
    }
  };

  const minDateTime = new Date().toISOString().slice(0, 16);

  return (
    <form onSubmit={handleSubmit} className="mt-3 p-3 bg-cream rounded-lg space-y-3">
      <div>
        <label className="block text-xs font-medium text-ink mb-1">Date & Time</label>
        <input
          type="datetime-local"
          value={scheduledTime}
          onChange={(e) => setScheduledTime(e.target.value)}
          min={minDateTime}
          className={`w-full px-3 py-1.5 text-sm border-2 rounded-lg bg-white text-ink focus:outline-none focus:border-terracotta ${
            errors.scheduled_time ? "border-error" : "border-cream-dark"
          }`}
        />
        {errors.scheduled_time && (
          <p className="mt-1 text-xs text-error">{errors.scheduled_time}</p>
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-ink mb-1">Meeting URL</label>
        <input
          type="url"
          value={meetingUrl}
          onChange={(e) => setMeetingUrl(e.target.value)}
          placeholder="https://zoom.us/j/..."
          className={`w-full px-3 py-1.5 text-sm border-2 rounded-lg bg-white text-ink placeholder-ink-faint focus:outline-none focus:border-terracotta ${
            errors.meeting_url ? "border-error" : "border-cream-dark"
          }`}
        />
        {errors.meeting_url && (
          <p className="mt-1 text-xs text-error">{errors.meeting_url}</p>
        )}
        <p className="mt-1 text-xs text-ink-faint">Zoom, Google Meet, Teams, or Whereby</p>
      </div>

      {apiError && <p className="text-xs text-error">{apiError}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={scheduleMeeting.isPending}
          className="px-3 py-1.5 text-sm bg-terracotta text-white font-medium rounded-lg hover:bg-terracotta-dark transition-colors disabled:opacity-50"
        >
          {scheduleMeeting.isPending ? "..." : "Schedule"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm border-2 border-cream-dark text-ink-muted rounded-lg hover:bg-cream transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function MeetingCard({ meeting, isMentor }: { meeting: Meeting; isMentor: boolean }) {
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const canSchedule = isMentor && meeting.status === "REQUESTED";

  return (
    <div className="p-3 bg-white border-2 border-cream-dark rounded-lg">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {meeting.scheduled_time ? (
            <p className="text-sm font-medium text-ink">{formatDateTime(meeting.scheduled_time)}</p>
          ) : (
            <p className="text-sm text-ink-faint italic">Not scheduled yet</p>
          )}
        </div>
        <MeetingStatusBadge status={meeting.status} />
      </div>

      {meeting.meeting_url && meeting.status === "SCHEDULED" && (
        <a
          href={meeting.meeting_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-2 text-xs font-medium text-terracotta hover:text-terracotta-dark"
        >
          Join Meeting →
        </a>
      )}

      {meeting.status === "COMPLETED" && (
        <Link
          href={`/meetings/${meeting.id}`}
          className="inline-block mt-2 text-xs font-medium text-terracotta hover:text-terracotta-dark"
        >
          View Details →
        </Link>
      )}

      {canSchedule && !showScheduleForm && (
        <button
          onClick={() => setShowScheduleForm(true)}
          className="mt-2 text-xs font-medium text-teal hover:text-teal-dark"
        >
          Schedule this meeting
        </button>
      )}

      {showScheduleForm && (
        <ScheduleMeetingForm meeting={meeting} onCancel={() => setShowScheduleForm(false)} />
      )}
    </div>
  );
}

function MeetingsSection({
  mentorshipId,
  isMentor,
  isMentee,
  isActive,
}: {
  mentorshipId: string;
  isMentor: boolean;
  isMentee: boolean;
  isActive: boolean;
}) {
  const { data: meetingsData, isLoading } = useMentorshipMeetings(mentorshipId);
  const requestMeeting = useRequestMeeting();
  const [requestError, setRequestError] = useState<string | null>(null);

  const meetings = meetingsData?.meetings ?? [];

  const handleRequestMeeting = async () => {
    setRequestError(null);
    try {
      await requestMeeting.mutateAsync(mentorshipId);
    } catch (err) {
      if (err instanceof ApiError) {
        setRequestError(err.message);
      } else {
        setRequestError("Failed to request meeting");
      }
    }
  };

  return (
    <div className="border-l border-cream-dark p-4 overflow-y-auto bg-cream/50">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-medium text-ink">Meetings</h2>
        {isMentee && isActive && (
          <button
            onClick={handleRequestMeeting}
            disabled={requestMeeting.isPending}
            className="px-3 py-1 text-xs bg-teal text-white font-medium rounded-lg hover:bg-teal-dark transition-colors disabled:opacity-50"
          >
            {requestMeeting.isPending ? "..." : "+ Request"}
          </button>
        )}
      </div>

      {requestError && <p className="text-xs text-error mb-3">{requestError}</p>}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-16 bg-cream-dark rounded-lg animate-pulse" />
          ))}
        </div>
      ) : meetings.length > 0 ? (
        <div className="space-y-3">
          {meetings.map((meeting) => (
            <MeetingCard key={meeting.id} meeting={meeting} isMentor={isMentor} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-ink-muted text-center py-8">
          No meetings yet
          {isMentee && isActive && (
            <>
              <br />
              <span className="text-xs">Request one to get started</span>
            </>
          )}
        </p>
      )}
    </div>
  );
}

function MessageBubble({ message, isOwnMessage }: { message: Message; isOwnMessage: boolean }) {
  return (
    <div className={`flex ${isOwnMessage ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isOwnMessage ? "bg-terracotta text-white" : "bg-white border-2 border-cream-dark text-ink"
        }`}
      >
        {!isOwnMessage && (
          <p className="text-xs font-medium mb-1 text-ink-muted">
            {message.sender?.display_name || message.sender?.email || "Unknown"}
          </p>
        )}
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <p className={`text-xs mt-1 ${isOwnMessage ? "text-terracotta-light" : "text-ink-faint"}`}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}

function MessageThread({
  mentorshipId,
  currentUserId,
  isActive,
}: {
  mentorshipId: string;
  currentUserId: string;
  isActive: boolean;
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  const { data: messagesData, isLoading } = useMessages(mentorshipId, { polling: isActive });

  const messages = messagesData?.messages ?? [];
  const sortedMessages = [...messages].reverse();

  useEffect(() => {
    if (shouldAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [sortedMessages.length, shouldAutoScroll]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShouldAutoScroll(isNearBottom);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-ink-muted">Loading messages...</p>
      </div>
    );
  }

  if (sortedMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-ink-muted">No messages yet. Start the conversation!</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-4 space-y-3">
      {sortedMessages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          isOwnMessage={message.sender_id === currentUserId}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function MessageInput({ mentorshipId, disabled }: { mentorshipId: string; disabled: boolean }) {
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const sendMessage = useSendMessage();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const result = messageSchema.safeParse({ body });
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Invalid message");
      return;
    }

    try {
      await sendMessage.mutateAsync({ mentorshipId, body: result.data.body });
      setBody("");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to send message");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-cream-dark p-4 bg-white">
      {error && <p className="text-sm text-error mb-2">{error}</p>}
      <div className="flex gap-2">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={disabled ? "Mentorship is not active" : "Type a message..."}
          disabled={disabled || sendMessage.isPending}
          rows={1}
          className="flex-1 px-4 py-2 border-2 border-cream-dark rounded-lg bg-white text-ink placeholder-ink-faint focus:outline-none focus:border-terracotta resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={disabled || sendMessage.isPending || !body.trim()}
          className="btn btn-primary"
        >
          {sendMessage.isPending ? "..." : "Send"}
        </button>
      </div>
    </form>
  );
}

export default function MentorshipPage() {
  const params = useParams();
  const mentorshipId = params.id as string;

  const { user } = useUser();
  const { data: mentorship, isLoading, error } = useMentorship(mentorshipId);
  const acceptMentorship = useAcceptMentorship();
  const endMentorship = useEndMentorship();

  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-ink-muted">Loading...</p>
      </main>
    );
  }

  if (error || !mentorship) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-4">
        <p className="text-ink-muted">
          {error instanceof ApiError ? error.message : "Mentorship not found"}
        </p>
        <Link href="/dashboard" className="text-sm text-terracotta hover:text-terracotta-dark">
          Back to Dashboard
        </Link>
      </main>
    );
  }

  const isMentor = user?.id === mentorship.mentor_id;
  const isMentee = user?.id === mentorship.mentee_id;
  const otherParty = isMentor ? mentorship.mentee : mentorship.mentor;
  const roleLabel = isMentor ? "You are the mentor" : "You are the mentee";
  const isActive = mentorship.status === "ACTIVE";
  const isRequested = mentorship.status === "REQUESTED";

  const handleAccept = async () => {
    setActionError(null);
    try {
      await acceptMentorship.mutateAsync(mentorshipId);
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to accept mentorship");
      }
    }
  };

  const handleEnd = async () => {
    setActionError(null);
    try {
      await endMentorship.mutateAsync(mentorshipId);
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to end mentorship");
      }
    }
  };

  return (
    <main className="flex flex-1 flex-col h-screen">
      <header className="border-b border-cream-dark bg-white shrink-0">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-sm text-ink-muted hover:text-ink transition-colors"
              >
                ← Dashboard
              </Link>
              <div className="h-4 w-px bg-cream-dark" />
              <div>
                <h1 className="font-display font-semibold text-ink">
                  {otherParty?.display_name || otherParty?.email || "Unknown"}
                </h1>
                <p className="text-sm text-ink-muted">{roleLabel}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium px-2 py-1 rounded ${statusStyles[mentorship.status] || statusStyles.ENDED}`}>
                {mentorship.status}
              </span>

              {isRequested && isMentor && (
                <button
                  onClick={handleAccept}
                  disabled={acceptMentorship.isPending}
                  className="px-4 py-1.5 text-sm bg-olive text-white font-medium rounded-lg hover:bg-olive-dark transition-colors disabled:opacity-50"
                >
                  {acceptMentorship.isPending ? "..." : "Accept"}
                </button>
              )}

              {isActive && (
                <button
                  onClick={handleEnd}
                  disabled={endMentorship.isPending}
                  className="px-4 py-1.5 text-sm border-2 border-cream-dark text-ink-muted font-medium rounded-lg hover:bg-cream transition-colors disabled:opacity-50"
                >
                  {endMentorship.isPending ? "..." : "End Mentorship"}
                </button>
              )}
            </div>
          </div>
          {actionError && <p className="mt-2 text-sm text-error">{actionError}</p>}
        </div>
      </header>

      {isRequested && isMentee && (
        <div className="bg-golden-light border-b border-golden px-6 py-3">
          <p className="text-sm text-golden-dark max-w-5xl mx-auto">
            Waiting for the mentor to accept your request. You can send messages while you wait.
          </p>
        </div>
      )}

      {mentorship.status === "ENDED" && (
        <div className="bg-cream border-b border-cream-dark px-6 py-3">
          <p className="text-sm text-ink-muted max-w-5xl mx-auto">
            This mentorship has ended. You can view the message history but cannot send new messages.
          </p>
        </div>
      )}

      {mentorship.status === "DECLINED" && (
        <div className="bg-error-light border-b border-error px-6 py-3">
          <p className="text-sm text-error max-w-5xl mx-auto">
            This mentorship request was declined.
          </p>
        </div>
      )}

      <div className="flex-1 flex min-h-0">
        <div className="flex-1 flex flex-col min-w-0">
          {user && (
            <MessageThread
              mentorshipId={mentorshipId}
              currentUserId={user.id}
              isActive={isActive || isRequested}
            />
          )}
          <MessageInput
            mentorshipId={mentorshipId}
            disabled={mentorship.status !== "ACTIVE" && mentorship.status !== "REQUESTED"}
          />
        </div>

        <div className="hidden md:block w-80 shrink-0">
          <MeetingsSection
            mentorshipId={mentorshipId}
            isMentor={isMentor}
            isMentee={isMentee}
            isActive={isActive}
          />
        </div>
      </div>

      <div className="md:hidden border-t border-cream-dark">
        <details className="group">
          <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-ink hover:bg-cream">
            Meetings
            <span className="ml-2 text-ink-faint group-open:rotate-180 inline-block transition-transform">▼</span>
          </summary>
          <div className="max-h-64 overflow-y-auto">
            <MeetingsSection
              mentorshipId={mentorshipId}
              isMentor={isMentor}
              isMentee={isMentee}
              isActive={isActive}
            />
          </div>
        </details>
      </div>
    </main>
  );
}
