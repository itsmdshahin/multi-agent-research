/**
 * useAuth — wraps the auth store with a redirect guard.
 * Call at the top of any protected page component.
 */
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";

export function useAuth(redirectTo = "/auth/login") {
  const router = useRouter();
  const { isAuthenticated, user, fetchMe, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      fetchMe().then(() => {
        if (!useAuthStore.getState().isAuthenticated) {
          router.push(redirectTo);
        }
      });
    }
  }, [isAuthenticated, isLoading]);

  return { user, isAuthenticated, isLoading };
}
