import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Topic, TopicListResponse } from "@/lib/types";

export function useTopics(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["topics", page, pageSize],
    queryFn: () =>
      apiFetch<TopicListResponse>(`/topics?page=${page}&page_size=${pageSize}`),
  });
}

export function useTopic(topicId: string | undefined) {
  return useQuery({
    queryKey: ["topic", topicId],
    queryFn: () => apiFetch<Topic>(`/topics/${topicId}`),
    enabled: !!topicId,
  });
}
