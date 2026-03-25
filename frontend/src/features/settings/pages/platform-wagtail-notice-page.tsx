"use client";

import { useRouter, Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export function PlatformWagtailNoticePage() {
  const router = useRouter();
  const t = useTranslations("Auth.platformWagtail");

  return (
    <div className="mx-auto flex w-full max-w-lg flex-col gap-6 px-4">
      <div className="space-y-2 text-center sm:text-start">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-start">
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
