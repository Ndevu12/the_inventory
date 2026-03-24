/** Client-side hint that the user explicitly chose a UI language (see I18N-08). */
export const LOCALE_STORAGE_KEY = "the-inventory.locale";

/**
 * Django's default language cookie name; set in parallel with next-intl's locale
 * cookie so a shared-origin API can read the same preference later (I18N-09+).
 */
export const DJANGO_LANGUAGE_COOKIE = "django_language";

const ONE_YEAR_SEC = 60 * 60 * 24 * 365;

export function persistLocalePreference(locale: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    /* quota / private mode */
  }
  document.cookie = `${DJANGO_LANGUAGE_COOKIE}=${encodeURIComponent(locale)};path=/;max-age=${ONE_YEAR_SEC};SameSite=Lax`;
}

export function hasExplicitLocalePreference(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(LOCALE_STORAGE_KEY) != null;
  } catch {
    return false;
  }
}
