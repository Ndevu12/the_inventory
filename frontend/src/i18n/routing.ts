import { defineRouting } from "next-intl/routing";

import rawConfig from "./locales-config.json";

export type LocaleEntry = {
  code: string;
  displayName: string;
  isRtl: boolean;
  isDefault?: boolean;
};

type LocalesConfig = {
  defaultLocale: string;
  locales: LocaleEntry[];
};

const config = rawConfig as LocalesConfig;

/** Metadata for each UI route locale (from Wagtail; run ``sync_frontend_locales`` after admin changes). */
export const localeEntries: readonly LocaleEntry[] = config.locales;

export const SUPPORTED_LOCALES = config.locales.map(
  (l) => l.code,
) as readonly string[];

export const DEFAULT_LOCALE = config.defaultLocale;

export const routing = defineRouting({
  locales: [...SUPPORTED_LOCALES],
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: "always",
});

export type AppLocale = string;
