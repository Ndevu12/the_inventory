"use client";

import { useEffect, useRef } from "react";
import { useLocale } from "next-intl";

import { usePathname, useRouter } from "@/i18n/navigation";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  hasExplicitLocalePreference,
  persistLocalePreference,
} from "@/lib/locale-preference";
import { routing } from "@/i18n/routing";

/**
 * When the user has not chosen a UI language, align the router with
 * `tenant.preferred_language` after `/auth/me/` loads (I18N-08 optional note).
 */
export function TenantLocaleSync() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const { data, isSuccess } = useMe();
  const didRun = useRef(false);

  useEffect(() => {
    if (!isSuccess || didRun.current) return;
    const pref = data?.tenant?.preferred_language;
    if (!pref) return;
    if (!routing.locales.includes(pref)) return;
    if (hasExplicitLocalePreference()) return;
    if (pref === locale) return;
    didRun.current = true;
    persistLocalePreference(pref);
    router.replace(pathname, { locale: pref });
  }, [data?.tenant?.preferred_language, isSuccess, locale, pathname, router]);

  return null;
}
