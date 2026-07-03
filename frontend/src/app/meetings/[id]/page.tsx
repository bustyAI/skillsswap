"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import { useUser } from "@/hooks/use-user";
import { useMeeting, useCancelMeeting, useCompleteMeeting } from "@/hooks/use-meetings";
import { useMeetingReview, useCreateReview, useUpdateReview } from "@/hooks/use-reviews";
import { ApiError } from "@/lib/api";

const reviewSchema = z.object({
  rating: z.number().min(1, "Please select a rating").max(5),
  comment: z
    .string()
    .max(2000, "Comment too long")
    .nullable()
    .transform((val) => val?.trim() || null),
});

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function StarRating({
  value,
  onChange,
  readonly = false,
}: {
  value: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
}) {
  const [hoverValue, setHoverValue] = useState(0);

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => onChange?.(star)}
          onMouseEnter={() => !readonly && setHoverValue(star)}
          onMouseLeave={() => setHoverValue(0)}
          className={`text-2xl transition-colors ${
            readonly ? "cursor-default" : "cursor-pointer"
          } ${
            star <= (hoverValue || value)
              ? "text-yellow-400"
              : "text-zinc-300 dark:text-zinc-600"
          }`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

function ReviewForm({
  meetingId,
  existingReview,
  editableUntil,
}: {
  meetingId: string;
  existingReview?: {
    rating: number;
    comment: string | null;
  };
  editableUntil?: string;
}) {
  const isEditing = !!existingReview;
  const createReview = useCreateReview();
  const updateReview = useUpdateReview();

  const [rating, setRating] = useState(existingReview?.rating ?? 0);
  const [comment, setComment] = useState(existingReview?.comment ?? "");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const isWithinEditWindow = editableUntil
    ? new Date(editableUntil) > new Date()
    : true;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    const result = reviewSchema.safeParse({ rating, comment: comment || null });
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Invalid review");
      return;
    }

    try {
      if (isEditing) {
        await updateReview.mutateAsync({
          meetingId,
          data: result.data,
        });
      } else {
        await createReview.mutateAsync({
          meetingId,
          data: result.data,
        });
      }
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to submit review");
      }
    }
  };

  const isPending = createReview.isPending || updateReview.isPending;

  if (isEditing && !isWithinEditWindow) {
    return (
      <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          The edit window for this review has closed.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Rating
        </label>
        <StarRating value={rating} onChange={setRating} />
        {rating === 0 && (
          <p className="mt-1 text-xs text-zinc-500">Click to rate</p>
        )}
      </div>

      <div>
        <label
          htmlFor="comment"
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2"
        >
          Comment (optional)
        </label>
        <textarea
          id="comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          placeholder="Share your experience..."
          className="w-full px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 resize-none"
        />
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {success && (
        <p className="text-sm text-green-600 dark:text-green-400">
          {isEditing ? "Review updated!" : "Review submitted!"}
        </p>
      )}

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={isPending || rating === 0}
          className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending ? "..." : isEditing ? "Update Review" : "Submit Review"}
        </button>

        {isEditing && editableUntil && (
          <p className="text-xs text-zinc-500">
            Editable until {formatDateTime(editableUntil)}
          </p>
        )}
      </div>
    </form>
  );
}

function ExistingReview({
  rating,
  comment,
  createdAt,
}: {
  rating: number;
  comment: string | null;
  createdAt: string;
}) {
  return (
    <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg">
      <div className="flex items-center gap-3 mb-2">
        <StarRating value={rating} readonly />
        <span className="text-sm text-zinc-500">
          {formatDateTime(createdAt)}
        </span>
      </div>
      {comment && (
        <p className="text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">
          {comment}
        </p>
      )}
    </div>
  );
}

export default function MeetingPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params.id as string;

  const { user } = useUser();
  const { data: meeting, isLoading, error } = useMeeting(meetingId);
  const { data: review, error: reviewError } = useMeetingReview(meetingId);
  const cancelMeeting = useCancelMeeting();
  const completeMeeting = useCompleteMeeting();

  const [actionError, setActionError] = useState<string | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </main>
    );
  }

  if (error || !meeting) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-4">
        <p className="text-zinc-500">
          {error instanceof ApiError ? error.message : "Meeting not found"}
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

  const mentorship = meeting.mentorship;
  const isMentee = user?.id === mentorship?.mentee_id;
  const isMentor = user?.id === mentorship?.mentor_id;
  const otherParty = isMentor ? mentorship?.mentee : mentorship?.mentor;

  const canCancel = meeting.status === "REQUESTED" || meeting.status === "SCHEDULED";
  const canComplete =
    meeting.status === "SCHEDULED" &&
    meeting.scheduled_time &&
    new Date(meeting.scheduled_time) <= new Date();

  const hasReview = review && !(reviewError instanceof ApiError && reviewError.status === 404);
  const canReview = isMentee && meeting.status === "COMPLETED";
  const isWithinEditWindow = review?.editable_until
    ? new Date(review.editable_until) > new Date()
    : false;

  const handleCancel = async () => {
    setActionError(null);
    try {
      await cancelMeeting.mutateAsync(meetingId);
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to cancel meeting");
      }
    }
  };

  const handleComplete = async () => {
    setActionError(null);
    try {
      await completeMeeting.mutateAsync(meetingId);
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to mark meeting as complete");
      }
    }
  };

  const statusStyles = {
    REQUESTED: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400",
    SCHEDULED: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
    COMPLETED: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400",
    CANCELLED: "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400",
  };

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-2xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              ← Back
            </button>
            <div className="h-4 w-px bg-zinc-200 dark:bg-zinc-700" />
            <h1 className="font-semibold text-zinc-900 dark:text-zinc-100">
              Meeting Details
            </h1>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-8 space-y-8">
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <span className={`text-sm px-3 py-1 rounded-full ${statusStyles[meeting.status]}`}>
              {meeting.status}
            </span>
          </div>

          {meeting.scheduled_time && (
            <div>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">Scheduled for</p>
              <p className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
                {formatDateTime(meeting.scheduled_time)}
              </p>
            </div>
          )}

          {meeting.meeting_url && meeting.status === "SCHEDULED" && (
            <div>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">Meeting link</p>
              <a
                href={meeting.meeting_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-900 dark:text-zinc-100 hover:underline break-all"
              >
                {meeting.meeting_url}
              </a>
            </div>
          )}

          {otherParty && (
            <div>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                {isMentor ? "Mentee" : "Mentor"}
              </p>
              <p className="text-zinc-900 dark:text-zinc-100">
                {otherParty.display_name || otherParty.email}
              </p>
            </div>
          )}

          {actionError && (
            <p className="text-sm text-red-600 dark:text-red-400">{actionError}</p>
          )}

          <div className="flex gap-3 pt-2">
            {canComplete && (
              <button
                onClick={handleComplete}
                disabled={completeMeeting.isPending}
                className="px-4 py-2 text-sm bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {completeMeeting.isPending ? "..." : "Mark as Complete"}
              </button>
            )}

            {canCancel && (
              <button
                onClick={handleCancel}
                disabled={cancelMeeting.isPending}
                className="px-4 py-2 text-sm border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 font-medium rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
              >
                {cancelMeeting.isPending ? "..." : "Cancel Meeting"}
              </button>
            )}

            {mentorship && (
              <Link
                href={`/mentorships/${mentorship.id}`}
                className="px-4 py-2 text-sm border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
              >
                View Mentorship
              </Link>
            )}
          </div>
        </section>

        {canReview && (
          <section className="border-t border-zinc-200 dark:border-zinc-700 pt-8">
            <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4">
              {hasReview ? "Your Review" : "Leave a Review"}
            </h2>

            {hasReview && !showEditForm ? (
              <div className="space-y-4">
                <ExistingReview
                  rating={review.rating}
                  comment={review.comment}
                  createdAt={review.created_at}
                />
                {isWithinEditWindow && (
                  <button
                    onClick={() => setShowEditForm(true)}
                    className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline"
                  >
                    Edit review
                  </button>
                )}
              </div>
            ) : (
              <ReviewForm
                meetingId={meetingId}
                existingReview={
                  hasReview
                    ? { rating: review.rating, comment: review.comment }
                    : undefined
                }
                editableUntil={review?.editable_until}
              />
            )}
          </section>
        )}

        {meeting.status === "COMPLETED" && isMentor && (
          <section className="border-t border-zinc-200 dark:border-zinc-700 pt-8">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              This meeting has been completed. The mentee can leave a review.
            </p>
          </section>
        )}
      </div>
    </main>
  );
}
