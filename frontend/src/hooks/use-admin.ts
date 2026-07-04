import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import type { AdminReportListResponse } from "@/lib/types";

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
