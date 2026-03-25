"use client";

import { useRouter as useNextRouter } from "next/navigation";
import { useEffect } from "react";
import { useLocale } from "next-intl";

import { usePathname, useRouter } from "@/i18n/navigation";
import { useMe } from "@/features/auth/hooks/use-auth";
import { setApiUiLocale } from "@/lib/api-ui-locale";
import {
  hasExplicitLocalePreference,
  syncDjangoLanguageCookie,
} from "@/lib/locale-preference";
import { routing } from "@/i18n/routing";

/**
 * When the operator has not used the language switcher, align the URL locale with
 * `tenant.preferred_language` after `/auth/me/` loads. Updates the Django language
 * cookie and API UI locale only — unlike the switcher, it does not persist
 * the explicit user key in `locale-preference.ts`, so later tenant default changes can
 * still apply on reload.
 */
export function TenantLocaleSync() {
  const locale = useLocale();
  const router = useRouter();
  const refresh = useNextRouter().refresh;
  const pathname = usePathname();
  const { data, isSuccess } = useMe();

  useEffect(() => {
    if (!isSuccess) return;
    const pref = data?.tenant?.preferred_language;
    if (!pref) return;
    if (!routing.locales.includes(pref)) return;
    if (hasExplicitLocalePreference()) return;
    if (pref === locale) return;
    syncDjangoLanguageCookie(pref);
    setApiUiLocale(pref);
    router.replace(pathname, { locale: pref });
    refresh();
  }, [
    data?.tenant?.preferred_language,
    isSuccess,
    locale,
    pathname,
    refresh,
    router,
  ]);

  return null;
}
