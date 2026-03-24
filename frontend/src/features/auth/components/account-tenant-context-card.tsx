"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "../context/auth-context";

export function AccountTenantContextCard() {
  const t = useTranslations("Auth.account");
  const { tenantSlug, memberships } = useAuth();
  const current = memberships.find((m) => m.tenant__slug === tenantSlug);

  if (!current) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("workspaceTitle")}</CardTitle>
          <CardDescription>{t("workspaceNoTenantDescription")}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t("workspaceTitle")}</CardTitle>
        <CardDescription>{t("workspaceDescription")}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <div>
          <p className="text-muted-foreground">{t("organisation")}</p>
          <p className="font-medium">{current.tenant__name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">{t("slug")}</p>
          <p className="font-mono text-xs">{current.tenant__slug}</p>
        </div>
        <div>
          <p className="text-muted-foreground">{t("yourRole")}</p>
          <p className="font-medium capitalize">{current.role}</p>
        </div>
      </CardContent>
    </Card>
  );
}
