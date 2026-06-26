import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";

interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
}

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
