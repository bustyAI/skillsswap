import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import type {
  AdminReportListResponse,
  AdminReport,
  ResolveReportRequest,
  ReportStatus,
  AdminUserListResponse,
  AdminActionResponse,
  AdminMentorListResponse,
} from "@/lib/types";

export function useAdminCheck() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const query = useQuery({
    queryKey: ["admin", "check"],
    queryFn: async () => {
      try {
        await apiFetch<AdminReportListResponse>("/admin/reports?page_size=1");
        return { isAdmin: true };
      } catch (error) {
        if (error instanceof ApiError && error.status === 403) {
          return { isAdmin: false };
        }
        throw error;
      }
    },
    enabled: isAuthenticated && !authLoading,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  return {
    isAdmin: query.data?.isAdmin ?? false,
    isLoading: authLoading || query.isLoading,
    error: query.error,
  };
}

export function useAdminReports(
  page: number = 1,
  pageSize: number = 20,
  statusFilter?: ReportStatus
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (statusFilter) {
    params.set("status", statusFilter);
  }

  return useQuery({
    queryKey: ["admin", "reports", page, pageSize, statusFilter],
    queryFn: () =>
      apiFetch<AdminReportListResponse>(`/admin/reports?${params.toString()}`),
  });
}

export function useResolveReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      reportId,
      data,
    }: {
      reportId: string;
      data: ResolveReportRequest;
    }) => {
      return apiFetch<AdminReport>(`/admin/reports/${reportId}/resolve`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "reports"] });
    },
  });
}

export function useAdminUserSearch(
  email: string,
  page: number = 1,
  pageSize: number = 20,
  includeBanned: boolean = true
) {
  const params = new URLSearchParams({
    email,
    page: page.toString(),
    page_size: pageSize.toString(),
    include_banned: includeBanned.toString(),
  });

  return useQuery({
    queryKey: ["admin", "users", "search", email, page, pageSize, includeBanned],
    queryFn: () =>
      apiFetch<AdminUserListResponse>(`/admin/users/search?${params.toString()}`),
    enabled: email.length > 0,
  });
}

export function useBanUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      reason,
    }: {
      userId: string;
      reason: string;
    }) => {
      return apiFetch<AdminActionResponse>(`/admin/users/${userId}/ban`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useAdminMentors(
  page: number = 1,
  pageSize: number = 20,
  enabledOnly: boolean = false
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    enabled_only: enabledOnly.toString(),
  });

  return useQuery({
    queryKey: ["admin", "mentors", page, pageSize, enabledOnly],
    queryFn: () =>
      apiFetch<AdminMentorListResponse>(`/admin/mentors?${params.toString()}`),
  });
}

export function useToggleMentorEnabled() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      reason,
    }: {
      userId: string;
      reason: string;
    }) => {
      return apiFetch<AdminActionResponse>(`/admin/mentors/${userId}/disable`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "mentors"] });
    },
  });
}
