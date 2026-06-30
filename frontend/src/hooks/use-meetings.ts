import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { MeetingListResponse } from "@/lib/types";

export function useMyMeetings() {
  return useQuery({
    queryKey: ["meetings", "me"],
    queryFn: () => apiFetch<MeetingListResponse>("/meetings/me"),
  });
}
