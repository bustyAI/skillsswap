import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import type { User, UserUpdateRequest } from "@/lib/types";

export function useUser() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const query = useQuery({
    queryKey: ["user", "me"],
    queryFn: () => apiFetch<User>("/users/me"),
    enabled: isAuthenticated && !authLoading,
    retry: false,
  });

  return {
    user: query.data ?? null,
    isLoading: authLoading || query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserUpdateRequest) => {
      return apiFetch<User>("/users/me", {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "me"] });
      // Also invalidate queries that contain user data
      queryClient.invalidateQueries({ queryKey: ["mentorships"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });
}
