"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

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
 * Waits for GET /auth/me/ bootstrap, then requires at least one organization
 * membership for dashboard routes. Otherwise redirects to `/no-organization`
 * or `/login` when cookie session verification fails.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const t = useTranslations("Auth.guard");
  const { isReady, memberships } = useAuth();
  const meQuery = useBootstrapAuth();

  useEffect(() => {
    if (!isReady) return;
    if (!meQuery.isFetched) return;
    if (meQuery.isError) {
      useAuthStore.getState().logout();
      router.replace("/login");
      return;
    }
    if (memberships.length === 0) {
      router.replace("/no-organization");
    }
  }, [
    isReady, meQuery.isFetched, meQuery.isError, memberships.length, router]);

  const awaitingBootstrap = !meQuery.isFetched;
  const sessionBlocked =
    meQuery.isFetched && !meQuery.isError && memberships.length === 0;

  if (
    !isReady ||
    awaitingBootstrap ||
    sessionBlocked ||
    (meQuery.isFetched && meQuery.isError)
  ) {
    return (
      <div className="flex h-screen w-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <p className="text-sm text-muted-foreground">{t("loading")}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
