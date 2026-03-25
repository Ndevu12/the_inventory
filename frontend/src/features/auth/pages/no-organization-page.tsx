"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

import { useAuth } from "../context/auth-context";
import { useBootstrapAuth } from "../hooks/use-auth";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";

export function NoOrganizationPage() {
  const router = useRouter();
  const t = useTranslations("Auth.noOrganization");
  const queryClient = useQueryClient();
  const { isReady, accessToken, memberships } = useAuth();
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const meQuery = useBootstrapAuth();

  const hasToken = !!(accessToken || refreshToken);

  useEffect(() => {
    if (!isReady) return;
    if (!hasToken) {
      router.replace("/login");
      return;
    }
    if (!meQuery.isFetched) return;
    if (meQuery.isError) {
      useAuthStore.getState().logout();
      queryClient.clear();
      router.replace("/login");
      return;
    }
    if (memberships.length > 0) {
      router.replace("/");
    }
  }, [
    isReady,
    hasToken,
    meQuery.isFetched,
    meQuery.isError,
    memberships.length,
    router,
    queryClient,
  ]);

  if (!isReady || !hasToken) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        <p className="text-sm text-muted-foreground">{t("loading")}</p>
      </div>
    );
  }

  if (!meQuery.isFetched || meQuery.isError) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        <p className="text-sm text-muted-foreground">{t("loading")}</p>
      </div>
    );
  }

  if (memberships.length > 0) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        <p className="text-sm text-muted-foreground">{t("loading")}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-lg flex-col gap-6 px-4">
      <div className="space-y-2 text-center sm:text-start">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
        <p className="text-sm text-muted-foreground">{t("platformHint")}</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-start">
        <Button
          type="button"
          variant="default"
          onClick={() => {
            useAuthStore.getState().logout();
            queryClient.clear();
            router.replace("/login");
          }}
        >
          {t("signOut")}
        </Button>
      </div>
    </div>
  );
}
