"use client";

import { useRouter, Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { getWagtailPlatformAuditLogUrl } from "@/lib/wagtail-admin-url";

type PlatformWagtailNoticePageProps = {
  /** When true, show a direct link to the Wagtail platform audit log snippet index. */
  showPlatformAuditWagtailLink?: boolean;
};

export function PlatformWagtailNoticePage({
  showPlatformAuditWagtailLink = false,
}: PlatformWagtailNoticePageProps) {
  const router = useRouter();
  const t = useTranslations("Auth.platformWagtail");
  const wagtailAuditUrl = getWagtailPlatformAuditLogUrl();

  return (
    <div className="mx-auto flex w-full max-w-lg flex-col gap-6 px-4">
      <div className="space-y-2 text-center sm:text-start">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-start">
        {showPlatformAuditWagtailLink ? (
          <div className="flex w-full flex-col gap-2 sm:w-auto">
            <Button
              type="button"
              render={
                <a
                  href={wagtailAuditUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                />
              }
            >
              {t("openPlatformAuditLog")}
            </Button>
            <p className="text-xs text-muted-foreground sm:w-full">
              {t("wagtailLinkNote")}
            </p>
          </div>
        ) : null}
        <Button type="button" onClick={() => router.push("/")}>
          {t("backHome")}
        </Button>
        <Button type="button" variant="outline" render={<Link href="/login" />}>
          {t("signInDifferent")}
        </Button>
      </div>
    </div>
  );
}
