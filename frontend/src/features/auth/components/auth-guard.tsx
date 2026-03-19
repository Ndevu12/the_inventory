"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/auth-context";
import { useBootstrapAuth } from "../hooks/use-auth";
import { useAuthStore } from "@/lib/auth-store";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * Protects dashboard routes. Only renders children when authenticated.
 * AuthProvider handles hydration gating; this only runs when isReady.
 *
 * We do NOT redirect on useBootstrapAuth isError: after login we have user/tenant
 * from the response, so bootstrap is skipped. On reload, if /me fails with 401,
 * api-client logs out and we redirect via the "no tokens" effect.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const { isReady, isAuthenticated, accessToken } = useAuth();
  const { refreshToken } = useAuthStore();
  const hasToken = !!accessToken;

  // Bootstrap only runs when we have tokens but no user (page reload). After login we skip.
  useBootstrapAuth();

  // Redirect only when we truly have no valid auth. api-client logs out on 401+refresh failure.
  useEffect(() => {
    if (!isReady) return;
    if (!hasToken) {
      router.replace("/login");
      return;
    }
    if (!isAuthenticated && !refreshToken) {
      router.replace("/login");
    }
  }, [isReady, hasToken, isAuthenticated, refreshToken, router]);

  if (!isReady || !hasToken) {
    return (
      <div className="flex h-screen w-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
