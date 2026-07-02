import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  MentorProfile,
  MentorProfileCreateRequest,
  MentorProfileUpdateRequest,
  MentorTopicsResponse,
  MyMentorProfile,
  RecommendationsResponse,
  ReviewListResponse,
  TopicMentorsResponse,
} from "@/lib/types";

export function useRecommendations(topicId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["recommendations", topicId],
    queryFn: () =>
      apiFetch<RecommendationsResponse>(`/recommendations?topic_id=${topicId}`),
    enabled: !!topicId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTopicMentors(
  topicId: string | undefined,
  page = 1,
  pageSize = 20
) {
  return useQuery({
    queryKey: ["topicMentors", topicId, page, pageSize],
    queryFn: () =>
      apiFetch<TopicMentorsResponse>(
        `/topics/${topicId}/mentors?page=${page}&page_size=${pageSize}`
      ),
    enabled: !!topicId,
  });
}

export function useMentorProfile(userId: string | undefined) {
  return useQuery({
    queryKey: ["mentorProfile", userId],
    queryFn: () => apiFetch<MentorProfile>(`/mentors/${userId}`),
    enabled: !!userId,
  });
}

export function useMentorTopics(userId: string | undefined) {
  return useQuery({
    queryKey: ["mentorTopics", userId],
    queryFn: () => apiFetch<MentorTopicsResponse>(`/mentors/${userId}/topics`),
    enabled: !!userId,
  });
}

export function useMentorReviews(
  userId: string | undefined,
  page = 1,
  pageSize = 10
) {
  return useQuery({
    queryKey: ["mentorReviews", userId, page, pageSize],
    queryFn: () =>
      apiFetch<ReviewListResponse>(
        `/mentors/${userId}/reviews?page=${page}&page_size=${pageSize}`
      ),
    enabled: !!userId,
  });
}

export function useMyMentorProfile() {
  return useQuery({
    queryKey: ["mentorProfile", "me"],
    queryFn: () => apiFetch<MyMentorProfile>("/mentors/me"),
    retry: false,
  });
}

export function useMyMentorTopics() {
  return useQuery({
    queryKey: ["mentorTopics", "me"],
    queryFn: () => apiFetch<MentorTopicsResponse>("/mentors/me/topics"),
    retry: false,
  });
}

export function useCreateMentorProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MentorProfileCreateRequest) => {
      return apiFetch<MyMentorProfile>("/mentors/me", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentorProfile", "me"] });
    },
  });
}

export function useUpdateMentorProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MentorProfileUpdateRequest) => {
      return apiFetch<MyMentorProfile>("/mentors/me", {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentorProfile", "me"] });
    },
  });
}

export function useUpdateMentorTopics() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (topicIds: string[]) => {
      return apiFetch<MentorTopicsResponse>("/mentors/me/topics", {
        method: "POST",
        body: JSON.stringify({ topic_ids: topicIds }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentorTopics", "me"] });
    },
  });
}
