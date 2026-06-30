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
