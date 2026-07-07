import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Message, MessageListResponse } from "@/lib/types";

export function useMessages(mentorshipId: string | undefined, options?: { polling?: boolean }) {
  return useQuery({
    queryKey: ["mentorships", mentorshipId, "messages"],
    queryFn: () => apiFetch<MessageListResponse>(`/mentorships/${mentorshipId}/messages`),
    enabled: !!mentorshipId,
    refetchInterval: options?.polling ? 5000 : false,
  });
}

interface SendMessageParams {
  mentorshipId: string;
  body: string;
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ mentorshipId, body }: SendMessageParams) => {
      return apiFetch<Message>(`/mentorships/${mentorshipId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content: body }),
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["mentorships", variables.mentorshipId, "messages"],
      });
    },
  });
}
