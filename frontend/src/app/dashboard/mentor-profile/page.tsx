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
      {topics.map((topic) => {
        const isSelected = selectedIds.includes(topic.id);
        return (
          <button
            key={topic.id}
            type="button"
            onClick={() => toggleTopic(topic.id)}
            disabled={disabled}
            className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
              isSelected
                ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
                : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
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

  const isPending =
    createProfile.isPending || updateProfile.isPending || updateTopics.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label
          htmlFor="headline"
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2"
        >
          Headline
        </label>
        <input
          type="text"
          id="headline"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="e.g., Senior Software Engineer with 10+ years experience"
          className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 ${
            errors.headline
              ? "border-red-500 dark:border-red-400"
              : "border-zinc-200 dark:border-zinc-700"
          }`}
        />
        {errors.headline && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400">
            {errors.headline}
          </p>
        )}
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          A short description that appears in search results
        </p>
      </div>

      <div>
        <label
          htmlFor="bio"
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2"
        >
          Bio
        </label>
        <textarea
          id="bio"
          rows={6}
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Tell potential mentees about your experience, expertise, and what you can help them with..."
          className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 resize-none ${
            errors.bio
              ? "border-red-500 dark:border-red-400"
              : "border-zinc-200 dark:border-zinc-700"
          }`}
        />
        {errors.bio && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400">
            {errors.bio}
          </p>
        )}
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          Minimum 50 characters
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Topics
        </label>
        {allTopics.length > 0 ? (
          <TopicSelector
            topics={allTopics}
            selectedIds={selectedTopicIds}
            onChange={setSelectedTopicIds}
            disabled={isPending}
          />
        ) : (
          <p className="text-zinc-500 dark:text-zinc-400">No topics available</p>
        )}
        {errors.topics && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            {errors.topics}
          </p>
        )}
        <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
          Select the topics you can mentor in ({selectedTopicIds.length} selected)
        </p>
      </div>

      {apiError && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{apiError}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm text-green-600 dark:text-green-400">
            {isNewProfile
              ? "Mentor profile created successfully"
              : "Mentor profile updated successfully"}
          </p>
        </div>
      )}

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={isPending}
          className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending
            ? "Saving..."
            : isNewProfile
            ? "Create Profile"
            : "Save Changes"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="px-6 py-2 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
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
        <p className="text-zinc-500">Loading...</p>
      </main>
    );
  }

  const initialTopicIds = myTopics?.topics?.map((t: TopicBrief) => t.id) || [];

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
          <Link
            href="/dashboard"
            className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </header>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-8">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
          {hasProfile ? "Edit Mentor Profile" : "Create Mentor Profile"}
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400 mb-8">
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
