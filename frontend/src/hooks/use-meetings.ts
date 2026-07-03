import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Meeting, MeetingListResponse, MeetingScheduleRequest } from "@/lib/types";

export function useMyMeetings() {
  return useQuery({
    queryKey: ["meetings", "me"],
    queryFn: () => apiFetch<MeetingListResponse>("/meetings/me"),
  });
}

export function useMeeting(meetingId: string | undefined) {
  return useQuery({
    queryKey: ["meetings", meetingId],
    queryFn: () => apiFetch<Meeting>(`/meetings/${meetingId}`),
    enabled: !!meetingId,
  });
}

export function useMentorshipMeetings(mentorshipId: string | undefined) {
  return useQuery({
    queryKey: ["mentorships", mentorshipId, "meetings"],
    queryFn: () => apiFetch<MeetingListResponse>(`/mentorships/${mentorshipId}/meetings`),
    enabled: !!mentorshipId,
  });
}

export function useRequestMeeting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (mentorshipId: string) => {
      return apiFetch<Meeting>(`/mentorships/${mentorshipId}/meetings`, {
        method: "POST",
        body: JSON.stringify({}),
      });
    },
    onSuccess: (_data, mentorshipId) => {
      queryClient.invalidateQueries({ queryKey: ["mentorships", mentorshipId, "meetings"] });
      queryClient.invalidateQueries({ queryKey: ["meetings", "me"] });
    },
  });
}

interface ScheduleMeetingParams {
  meetingId: string;
  data: MeetingScheduleRequest;
}

export function useScheduleMeeting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ meetingId, data }: ScheduleMeetingParams) => {
      return apiFetch<Meeting>(`/meetings/${meetingId}/schedule`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["mentorships", data.mentorship_id, "meetings"] });
    },
  });
}

export function useCancelMeeting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (meetingId: string) => {
      return apiFetch<Meeting>(`/meetings/${meetingId}/cancel`, {
        method: "POST",
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["mentorships", data.mentorship_id, "meetings"] });
    },
  });
}

export function useCompleteMeeting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (meetingId: string) => {
      return apiFetch<Meeting>(`/meetings/${meetingId}/complete`, {
        method: "POST",
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["mentorships", data.mentorship_id, "meetings"] });
    },
  });
}
