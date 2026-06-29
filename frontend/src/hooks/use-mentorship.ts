import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Mentorship } from "@/lib/types";

interface CreateMentorshipParams {
  mentorId: string;
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
