import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Review, ReviewCreate, ReviewUpdate } from "@/lib/types";

export function useMeetingReview(meetingId: string | undefined) {
  return useQuery({
    queryKey: ["meetings", meetingId, "review"],
    queryFn: () => apiFetch<Review>(`/meetings/${meetingId}/review`),
    enabled: !!meetingId,
    retry: false,
  });
}

interface CreateReviewParams {
  meetingId: string;
  data: ReviewCreate;
}

export function useCreateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ meetingId, data }: CreateReviewParams) => {
      return apiFetch<Review>(`/meetings/${meetingId}/review`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["meetings", variables.meetingId, "review"] });
      queryClient.invalidateQueries({ queryKey: ["meetings", variables.meetingId] });
      queryClient.invalidateQueries({ queryKey: ["mentorReviews"] });
    },
  });
}

interface UpdateReviewParams {
  meetingId: string;
  data: ReviewUpdate;
}

export function useUpdateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ meetingId, data }: UpdateReviewParams) => {
      return apiFetch<Review>(`/meetings/${meetingId}/review`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["meetings", variables.meetingId, "review"] });
      queryClient.invalidateQueries({ queryKey: ["mentorReviews"] });
    },
  });
}
