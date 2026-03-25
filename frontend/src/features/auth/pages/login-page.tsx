"use client";

import { useEffect, useMemo } from "react";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { Package, Box, AlertCircle, Search, Zap } from "lucide-react";
import { useTranslations } from "next-intl";

import { useAuth } from "../context/auth-context";
import { LoginForm } from "../components/login-form";
import { AuthMarketingShell } from "../components/auth-marketing-shell";
import { useLogin, useAuthConfig } from "../hooks/use-auth";
import { useLoginFormStore } from "../stores/login-form-store";
import type { LoginFormValues } from "../helpers/auth-schemas";

function LoginPageRegisterLink() {
  const t = useTranslations("Auth.login");
  const { data: config } = useAuthConfig();
  if (!config?.allow_registration) return null;
  return (
    <p className="text-center text-sm text-muted-foreground">
      {t("noOrgPrompt")}{" "}
      <Link
        href="/register"
        className="text-primary underline hover:no-underline"
      >
        {t("createOrgLink")}
      </Link>
    </p>
  );
}

export function LoginPage() {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations("Auth");
  const tMarketing = useTranslations("Auth.marketing");
  const { isReady, isAuthenticated } = useAuth();
  const loginMutation = useLogin();
  const { serverError, setServerError, reset } = useLoginFormStore();

  const marketingFeatures = useMemo(
    () => [
      {
        icon: Box,
        title: tMarketing("catalogTitle"),
        description: tMarketing("catalogDescription"),
      },
      {
        icon: Zap,
        title: tMarketing("trackingTitle"),
        description: tMarketing("trackingDescription"),
      },
      {
        icon: AlertCircle,
        title: tMarketing("alertsTitle"),
        description: tMarketing("alertsDescription"),
      },
      {
        icon: Search,
        title: tMarketing("searchTitle"),
        description: tMarketing("searchDescription"),
      },
    ],
    [tMarketing],
  );

  useEffect(() => {
    if (!isReady) return;
    if (pathname !== "/login") return;
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isReady, isAuthenticated, pathname, router]);

  useEffect(() => {
    return () => reset();
  }, [reset]);

  function handleSubmit(values: LoginFormValues) {
    setServerError(null);
    loginMutation.mutate(values, {
      onError: (error) => {
        const message =
          (error as { message?: string }).message ??
          t("invalidCredentials");
        setServerError(message);
      },
    });
  }

  return (
    <AuthMarketingShell
      columnAlign="center"
      formIcon={Package}
      title={t("login.title")}
      subtitle={t("login.subtitle")}
      marketingTitle={tMarketing("title")}
      marketingSubtitle={tMarketing("subtitle")}
      features={marketingFeatures}
    >
      <div className="space-y-4">
        <LoginForm
          onSubmit={handleSubmit}
          isPending={loginMutation.isPending}
          serverError={serverError}
        />
        <LoginPageRegisterLink />
      </div>
    </AuthMarketingShell>
  );
}
