"use client";

import { useEffect } from "react";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { Package, Box, AlertCircle, Search, Zap } from "lucide-react";
import { useTranslations } from "next-intl";

import { useAuth } from "../context/auth-context";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoginForm } from "../components/login-form";
import { FeatureCard } from "../components/feature-card";
import { FeaturesList } from "../components/feature-list";
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
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl grid grid-cols-1 gap-8 md:grid-cols-2 items-center">
        <div>
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <Package className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">{t("login.title")}</CardTitle>
              <CardDescription>{t("login.subtitle")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <LoginForm
                onSubmit={handleSubmit}
                isPending={loginMutation.isPending}
                serverError={serverError}
              />
              <LoginPageRegisterLink />
            </CardContent>
          </Card>
        </div>

        <div className="hidden md:block">
          <FeaturesList
            title={tMarketing("title")}
            subtitle={tMarketing("subtitle")}
          >
            <FeatureCard
              icon={Box}
              title={tMarketing("catalogTitle")}
              description={tMarketing("catalogDescription")}
            />
            <FeatureCard
              icon={Zap}
              title={tMarketing("trackingTitle")}
              description={tMarketing("trackingDescription")}
            />
            <FeatureCard
              icon={AlertCircle}
              title={tMarketing("alertsTitle")}
              description={tMarketing("alertsDescription")}
            />
            <FeatureCard
              icon={Search}
              title={tMarketing("searchTitle")}
              description={tMarketing("searchDescription")}
            />
          </FeaturesList>
        </div>
      </div>
    </div>
  );
}
