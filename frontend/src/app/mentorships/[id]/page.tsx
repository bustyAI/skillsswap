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

function MeetingStatusBadge({ status }: { status: Meeting["status"] }) {
  const styles = {
    REQUESTED: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400",
    SCHEDULED: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
    COMPLETED: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400",
    CANCELLED: "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400",
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded ${styles[status]}`}>
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
    <form onSubmit={handleSubmit} className="mt-3 p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg space-y-3">
      <div>
        <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
          Date & Time
        </label>
        <input
          type="datetime-local"
          value={scheduledTime}
          onChange={(e) => setScheduledTime(e.target.value)}
          min={minDateTime}
          className={`w-full px-3 py-1.5 text-sm border rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 ${
            errors.scheduled_time ? "border-red-500" : "border-zinc-200 dark:border-zinc-700"
          }`}
        />
        {errors.scheduled_time && (
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.scheduled_time}</p>
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
          Meeting URL
        </label>
        <input
          type="url"
          value={meetingUrl}
          onChange={(e) => setMeetingUrl(e.target.value)}
          placeholder="https://zoom.us/j/..."
          className={`w-full px-3 py-1.5 text-sm border rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 ${
            errors.meeting_url ? "border-red-500" : "border-zinc-200 dark:border-zinc-700"
          }`}
        />
        {errors.meeting_url && (
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.meeting_url}</p>
        )}
        <p className="mt-1 text-xs text-zinc-500">
          Zoom, Google Meet, Teams, or Whereby links only
        </p>
      </div>

      {apiError && (
        <p className="text-xs text-red-600 dark:text-red-400">{apiError}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={scheduleMeeting.isPending}
          className="px-3 py-1.5 text-sm bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50"
        >
          {scheduleMeeting.isPending ? "..." : "Schedule"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function MeetingCard({
  meeting,
  isMentor,
}: {
  meeting: Meeting;
  isMentor: boolean;
}) {
  const [showScheduleForm, setShowScheduleForm] = useState(false);

  const canSchedule = isMentor && meeting.status === "REQUESTED";

  return (
    <div className="p-3 border border-zinc-200 dark:border-zinc-700 rounded-lg">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {meeting.scheduled_time ? (
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              {formatDateTime(meeting.scheduled_time)}
            </p>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400 italic">
              Not scheduled yet
            </p>
          )}
        </div>
        <MeetingStatusBadge status={meeting.status} />
      </div>

      {meeting.meeting_url && meeting.status === "SCHEDULED" && (
        <a
          href={meeting.meeting_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-2 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
        >
          Join Meeting →
        </a>
      )}

      {meeting.status === "COMPLETED" && (
        <Link
          href={`/meetings/${meeting.id}`}
          className="inline-block mt-2 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
        >
          View Details →
        </Link>
      )}

      {canSchedule && !showScheduleForm && (
        <button
          onClick={() => setShowScheduleForm(true)}
          className="mt-2 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
        >
          Schedule this meeting
        </button>
      )}

      {showScheduleForm && (
        <ScheduleMeetingForm
          meeting={meeting}
          onCancel={() => setShowScheduleForm(false)}
        />
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
    <div className="border-l border-zinc-200 dark:border-zinc-700 p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-medium text-zinc-900 dark:text-zinc-100">Meetings</h2>
        {isMentee && isActive && (
          <button
            onClick={handleRequestMeeting}
            disabled={requestMeeting.isPending}
            className="px-3 py-1 text-xs bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50"
          >
            {requestMeeting.isPending ? "..." : "+ Request"}
          </button>
        )}
      </div>

      {requestError && (
        <p className="text-xs text-red-600 dark:text-red-400 mb-3">{requestError}</p>
      )}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : meetings.length > 0 ? (
        <div className="space-y-3">
          {meetings.map((meeting) => (
            <MeetingCard key={meeting.id} meeting={meeting} isMentor={isMentor} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 dark:text-zinc-400 text-center py-8">
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

function MessageBubble({
  message,
  isOwnMessage,
}: {
  message: Message;
  isOwnMessage: boolean;
}) {
  return (
    <div className={`flex ${isOwnMessage ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isOwnMessage
            ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
            : "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
        }`}
      >
        {!isOwnMessage && (
          <p className="text-xs font-medium mb-1 opacity-70">
            {message.sender?.display_name || message.sender?.email || "Unknown"}
          </p>
        )}
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <p
          className={`text-xs mt-1 ${
            isOwnMessage ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-500"
          }`}
        >
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

  const { data: messagesData, isLoading } = useMessages(mentorshipId, {
    polling: isActive,
  });

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
        <p className="text-zinc-500">Loading messages...</p>
      </div>
    );
  }

  if (sortedMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">
          No messages yet. Start the conversation!
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4 space-y-3"
    >
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

function MessageInput({
  mentorshipId,
  disabled,
}: {
  mentorshipId: string;
  disabled: boolean;
}) {
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
    <form onSubmit={handleSubmit} className="border-t border-zinc-200 dark:border-zinc-700 p-4">
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400 mb-2">{error}</p>
      )}
      <div className="flex gap-2">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={disabled ? "Mentorship is not active" : "Type a message..."}
          disabled={disabled || sendMessage.isPending}
          rows={1}
          className="flex-1 px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
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
          className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
        <p className="text-zinc-500">Loading...</p>
      </main>
    );
  }

  if (error || !mentorship) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-4">
        <p className="text-zinc-500">
          {error instanceof ApiError ? error.message : "Mentorship not found"}
        </p>
        <Link
          href="/dashboard"
          className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
        >
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
      <header className="border-b border-zinc-200 dark:border-zinc-800 shrink-0">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                ← Dashboard
              </Link>
              <div className="h-4 w-px bg-zinc-200 dark:bg-zinc-700" />
              <div>
                <h1 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {otherParty?.display_name || otherParty?.email || "Unknown"}
                </h1>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">{roleLabel}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
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

              {isRequested && isMentor && (
                <button
                  onClick={handleAccept}
                  disabled={acceptMentorship.isPending}
                  className="px-4 py-1.5 text-sm bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {acceptMentorship.isPending ? "..." : "Accept"}
                </button>
              )}

              {isActive && (
                <button
                  onClick={handleEnd}
                  disabled={endMentorship.isPending}
                  className="px-4 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
                >
                  {endMentorship.isPending ? "..." : "End Mentorship"}
                </button>
              )}
            </div>
          </div>
          {actionError && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">{actionError}</p>
          )}
        </div>
      </header>

      {isRequested && isMentee && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-6 py-3">
          <p className="text-sm text-yellow-700 dark:text-yellow-400 max-w-4xl mx-auto">
            Waiting for the mentor to accept your request. You can send messages while you wait.
          </p>
        </div>
      )}

      {mentorship.status === "ENDED" && (
        <div className="bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-200 dark:border-zinc-700 px-6 py-3">
          <p className="text-sm text-zinc-600 dark:text-zinc-400 max-w-4xl mx-auto">
            This mentorship has ended. You can view the message history but cannot send new messages.
          </p>
        </div>
      )}

      {mentorship.status === "DECLINED" && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-6 py-3">
          <p className="text-sm text-red-700 dark:text-red-400 max-w-4xl mx-auto">
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

      <div className="md:hidden border-t border-zinc-200 dark:border-zinc-700">
        <details className="group">
          <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
            Meetings
            <span className="ml-2 text-zinc-400 group-open:rotate-180 inline-block transition-transform">▼</span>
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
