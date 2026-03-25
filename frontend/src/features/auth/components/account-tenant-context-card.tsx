"use client";

import { useTranslations } from "next-intl";

import { useAuth } from "../context/auth-context";

const WORKSPACE_HEADING_ID = "account-workspace-summary-heading";

export function AccountTenantContextCard() {
  const t = useTranslations("Auth.account");
  const { tenantSlug, memberships } = useAuth();
  const current = memberships.find((m) => m.tenant__slug === tenantSlug);

  return (
    <section
      aria-labelledby={WORKSPACE_HEADING_ID}
      className="rounded-lg border border-border/60 bg-muted/40 px-4 py-3"
    >
      <h2
        id={WORKSPACE_HEADING_ID}
        className="text-sm font-medium text-foreground"
      >
        {t("workspaceTitle")}
      </h2>
      {current ? (
        <>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("workspaceDescription")}
          </p>
          <dl className="mt-3 flex flex-wrap gap-x-8 gap-y-3 text-sm">
            <div className="min-w-[8rem]">
              <dt className="text-muted-foreground">{t("organisation")}</dt>
              <dd className="font-medium">{current.tenant__name}</dd>
            </div>
            <div className="min-w-[8rem]">
              <dt className="text-muted-foreground">{t("slug")}</dt>
              <dd className="font-mono text-xs">{current.tenant__slug}</dd>
            </div>
            <div className="min-w-[8rem]">
              <dt className="text-muted-foreground">{t("yourRole")}</dt>
              <dd className="font-medium capitalize">{current.role}</dd>
            </div>
          </dl>
        </>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">
          {t("workspaceNoTenantDescription")}
        </p>
      )}
    </section>
  );
}
