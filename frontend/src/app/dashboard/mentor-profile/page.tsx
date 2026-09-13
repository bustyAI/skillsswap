"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { z } from "zod";
import {
  useMyMentorProfile,
  useMyMentorTopics,
  useCreateMentorProfile,
  useUpdateMentorProfile,
  useUpdateMentorTopics,
} from "@/hooks/use-mentors";
import { useTopics } from "@/hooks/use-topics";
import { ApiError } from "@/lib/api";
import type { Topic, TopicBrief } from "@/lib/types";

const mentorProfileSchema = z.object({
  headline: z
    .string()
    .min(10, "Headline must be at least 10 characters")
    .max(200, "Headline must be less than 200 characters")
    .nullable()
    .transform((val) => val?.trim() || null),
  bio: z
    .string()
    .min(50, "Bio must be at least 50 characters")
    .max(2000, "Bio must be less than 2000 characters")
    .nullable()
    .transform((val) => val?.trim() || null),
});

const topicColors = [
  { selected: "bg-terracotta text-white", unselected: "bg-terracotta-light text-terracotta-dark hover:bg-terracotta hover:text-white" },
  { selected: "bg-olive text-white", unselected: "bg-olive-light text-olive-dark hover:bg-olive hover:text-white" },
  { selected: "bg-golden text-white", unselected: "bg-golden-light text-golden-dark hover:bg-golden hover:text-white" },
  { selected: "bg-teal text-white", unselected: "bg-teal-light text-teal-dark hover:bg-teal hover:text-white" },
];

function TopicSelector({
  topics,
  selectedIds,
  onChange,
  disabled,
}: {
  topics: Topic[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}) {
  const toggleTopic = (topicId: string) => {
    if (disabled) return;
    if (selectedIds.includes(topicId)) {
      onChange(selectedIds.filter((id) => id !== topicId));
    } else {
      onChange([...selectedIds, topicId]);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {topics.map((topic, index) => {
        const isSelected = selectedIds.includes(topic.id);
        const colorScheme = topicColors[index % topicColors.length];
        return (
          <button
            key={topic.id}
            type="button"
            onClick={() => toggleTopic(topic.id)}
            disabled={disabled}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              isSelected ? colorScheme.selected : colorScheme.unselected
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            {topic.name}
            {isSelected && <span className="ml-1">×</span>}
          </button>
        );
      })}
    </div>
  );
}

interface MentorFormProps {
  isNewProfile: boolean;
  initialHeadline: string | null;
  initialBio: string | null;
  initialTopicIds: string[];
  allTopics: Topic[];
}

function MentorForm({
  isNewProfile,
  initialHeadline,
  initialBio,
  initialTopicIds,
  allTopics,
}: MentorFormProps) {
  const router = useRouter();
  const createProfile = useCreateMentorProfile();
  const updateProfile = useUpdateMentorProfile();
  const updateTopics = useUpdateMentorTopics();

  const [headline, setHeadline] = useState(initialHeadline || "");
  const [bio, setBio] = useState(initialBio || "");
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>(initialTopicIds);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setApiError(null);
    setSuccess(false);

    const result = mentorProfileSchema.safeParse({
      headline: headline || null,
      bio: bio || null,
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

    if (selectedTopicIds.length === 0) {
      setErrors({ topics: "Please select at least one topic" });
      return;
    }

    try {
      if (isNewProfile) {
        await createProfile.mutateAsync(result.data);
      } else {
        await updateProfile.mutateAsync(result.data);
      }
      await updateTopics.mutateAsync(selectedTopicIds);
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err.message);
      } else {
        setApiError("An unexpected error occurred");
      }
    }
  };

  const isPending = createProfile.isPending || updateProfile.isPending || updateTopics.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="headline" className="block text-sm font-medium text-ink mb-2">
          Headline
        </label>
        <input
          type="text"
          id="headline"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="e.g., Senior Software Engineer with 10+ years experience"
          className={`input ${errors.headline ? "border-error" : ""}`}
        />
        {errors.headline && (
          <p className="mt-1 text-sm text-error">{errors.headline}</p>
        )}
        <p className="mt-1 text-xs text-ink-faint">
          A short description that appears in search results
        </p>
      </div>

      <div>
        <label htmlFor="bio" className="block text-sm font-medium text-ink mb-2">
          Bio
        </label>
        <textarea
          id="bio"
          rows={6}
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Tell potential mentees about your experience, expertise, and what you can help them with..."
          className={`input resize-none ${errors.bio ? "border-error" : ""}`}
        />
        {errors.bio && (
          <p className="mt-1 text-sm text-error">{errors.bio}</p>
        )}
        <p className="mt-1 text-xs text-ink-faint">Minimum 50 characters</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-ink mb-2">Topics</label>
        {allTopics.length > 0 ? (
          <TopicSelector
            topics={allTopics}
            selectedIds={selectedTopicIds}
            onChange={setSelectedTopicIds}
            disabled={isPending}
          />
        ) : (
          <p className="text-ink-muted">No topics available</p>
        )}
        {errors.topics && (
          <p className="mt-2 text-sm text-error">{errors.topics}</p>
        )}
        <p className="mt-2 text-xs text-ink-faint">
          Select the topics you can mentor in ({selectedTopicIds.length} selected)
        </p>
      </div>

      {apiError && (
        <div className="p-4 bg-error-light rounded-lg">
          <p className="text-sm text-error">{apiError}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-success-light rounded-lg">
          <p className="text-sm text-success">
            {isNewProfile ? "Mentor profile created successfully" : "Mentor profile updated successfully"}
          </p>
        </div>
      )}

      <div className="flex items-center gap-4">
        <button type="submit" disabled={isPending} className="btn btn-primary">
          {isPending ? "Saving..." : isNewProfile ? "Create Profile" : "Save Changes"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="btn btn-secondary"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function MentorProfilePage() {
  const {
    data: mentorProfile,
    isLoading: profileLoading,
    error: fetchError,
  } = useMyMentorProfile();
  const { data: myTopics, isLoading: myTopicsLoading } = useMyMentorTopics();
  const { data: allTopics, isLoading: topicsLoading } = useTopics(1, 100);

  const isNewProfile = fetchError instanceof ApiError && fetchError.status === 404;
  const hasProfile = !!mentorProfile && !isNewProfile;
  const isLoading = profileLoading || myTopicsLoading || topicsLoading;

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-ink-muted">Loading...</p>
      </main>
    );
  }

  const initialTopicIds = myTopics?.topics?.map((t: TopicBrief) => t.id) || [];

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b border-cream-dark bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display text-xl font-bold text-ink">
            SkillSwap
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-ink-muted hover:text-ink transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </header>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-8">
        <h1 className="font-display text-2xl text-ink mb-2">
          {hasProfile ? "Edit Mentor Profile" : "Create Mentor Profile"}
        </h1>
        <p className="text-ink-muted mb-8">
          {hasProfile
            ? "Update your mentor profile to attract mentees."
            : "Set up your mentor profile to start accepting mentees."}
        </p>

        <MentorForm
          key={mentorProfile?.id || "new"}
          isNewProfile={!hasProfile}
          initialHeadline={mentorProfile?.headline || null}
          initialBio={mentorProfile?.bio || null}
          initialTopicIds={initialTopicIds}
          allTopics={allTopics?.items || []}
        />
      </div>
    </main>
  );
}
