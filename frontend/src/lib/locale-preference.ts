/**
 * Legacy key: older builds stored both user and tenant-applied locales here.
 * Still honored by {@link hasExplicitLocalePreference} so existing sessions keep
 * “I picked this language” behavior after upgrade.
 */
export const LOCALE_STORAGE_KEY = "the-inventory.locale";

/** Set only when the operator uses the language switcher (not tenant default sync). */
export const LOCALE_USER_EXPLICIT_STORAGE_KEY = "the-inventory.locale.explicit";

/**
 * Django's default language cookie name; set in parallel with next-intl's locale
 * cookie so a shared-origin API can read the same preference later (I18N-09+).
 */
export const DJANGO_LANGUAGE_COOKIE = "django_language";

const ONE_YEAR_SEC = 60 * 60 * 24 * 365;

export function syncDjangoLanguageCookie(locale: string): void {
  if (typeof window === "undefined") return;
  document.cookie = `${DJANGO_LANGUAGE_COOKIE}=${encodeURIComponent(locale)};path=/;max-age=${ONE_YEAR_SEC};SameSite=Lax`;
}

/** Persists an explicit operator choice (language switcher). Updates cookie + storage. */
export function persistLocalePreference(locale: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LOCALE_USER_EXPLICIT_STORAGE_KEY, locale);
  } catch {
    /* quota / private mode */
  }
  syncDjangoLanguageCookie(locale);
}

export function hasExplicitLocalePreference(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return (
      localStorage.getItem(LOCALE_USER_EXPLICIT_STORAGE_KEY) != null ||
      localStorage.getItem(LOCALE_STORAGE_KEY) != null
    );
  } catch {
    return false;
  }
}
