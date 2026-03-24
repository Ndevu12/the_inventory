import { defineRouting } from "next-intl/routing";

/** Supported UI locales (browser / cookie / URL; tenant sync is separate). */
export const SUPPORTED_LOCALES = ["en", "fr", "sw", "rw", "es", "ar"] as const;

export const DEFAULT_LOCALE = "en" as const;

export const routing = defineRouting({
  locales: [...SUPPORTED_LOCALES],
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: "always",
});

export type AppLocale = (typeof routing.locales)[number];
