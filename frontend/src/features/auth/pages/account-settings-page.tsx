"use client";

import { useTranslations } from "next-intl";

import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "../context/auth-context";
import { useMe } from "../hooks/use-auth";
import { AccountProfileForm } from "../components/account-profile-form";
import { AccountPasswordForm } from "../components/account-password-form";
import { AccountTenantContextCard } from "../components/account-tenant-context-card";

export function AccountSettingsPage() {
  const t = useTranslations("Auth.account");
  const { user } = useAuth();
  const { isLoading } = useMe();

  if (isLoading && !user) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-56" />
          <Skeleton className="h-4 w-80" />
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-72 rounded-xl lg:col-span-2" />
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-64 rounded-xl lg:col-span-2" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
        <p className="text-muted-foreground">{t("loadError")}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("pageTitle")}
        description={t("pageDescription")}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <AccountProfileForm user={user} />
          <AccountPasswordForm />
        </div>
        <div className="lg:col-span-1">
          <AccountTenantContextCard />
        </div>
      </div>
    </div>
  );
}
