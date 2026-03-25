"use client";

import { useTranslations } from "next-intl";

import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
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
        <div className="space-y-2 rounded-lg border border-border/60 bg-muted/20 p-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-3 w-full max-w-md" />
          <div className="mt-3 flex flex-wrap gap-6">
            <Skeleton className="h-12 w-32" />
            <Skeleton className="h-12 w-28" />
            <Skeleton className="h-12 w-24" />
          </div>
        </div>
        <div className="space-y-4">
          <Skeleton className="h-8 w-[220px] rounded-lg" />
          <Skeleton className="min-h-[280px] w-full max-w-2xl rounded-xl" />
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

      <AccountTenantContextCard />

      <Tabs defaultValue="profile" className="w-full max-w-2xl">
        <TabsList>
          <TabsTrigger value="profile">{t("tabs.profile")}</TabsTrigger>
          <TabsTrigger value="security">{t("tabs.security")}</TabsTrigger>
        </TabsList>
        <TabsContent value="profile" className="mt-4">
          <AccountProfileForm user={user} />
        </TabsContent>
        <TabsContent value="security" className="mt-4">
          <AccountPasswordForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}
