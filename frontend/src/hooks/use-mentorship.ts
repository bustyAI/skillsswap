import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Mentorship, MentorshipListResponse } from "@/lib/types";

interface CreateMentorshipParams {
  mentorId: string;
}

export function useMyMentorships() {
  return useQuery({
    queryKey: ["mentorships", "me"],
    queryFn: () => apiFetch<MentorshipListResponse>("/mentorships/me"),
  });
}

export function useMentorship(mentorshipId: string | undefined) {
  return useQuery({
    queryKey: ["mentorships", mentorshipId],
    queryFn: () => apiFetch<Mentorship>(`/mentorships/${mentorshipId}`),
    enabled: !!mentorshipId,
  });
}

export function useCreateMentorship() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ mentorId }: CreateMentorshipParams) => {
      return apiFetch<Mentorship>("/mentorships", {
        method: "POST",
        body: JSON.stringify({ mentor_id: mentorId }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentorships"] });
    },
  });
}

export function useAcceptMentorship() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (mentorshipId: string) => {
      return apiFetch<Mentorship>(`/mentorships/${mentorshipId}/accept`, {
        method: "POST",
      });
    },
    onSuccess: (_data, mentorshipId) => {
      queryClient.invalidateQueries({ queryKey: ["mentorships"] });
      queryClient.invalidateQueries({ queryKey: ["mentorships", mentorshipId] });
    },
  });
}

export function useEndMentorship() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (mentorshipId: string) => {
      return apiFetch<Mentorship>(`/mentorships/${mentorshipId}/end`, {
        method: "POST",
      });
    },
    onSuccess: (_data, mentorshipId) => {
      queryClient.invalidateQueries({ queryKey: ["mentorships"] });
      queryClient.invalidateQueries({ queryKey: ["mentorships", mentorshipId] });
    },
  });
}
