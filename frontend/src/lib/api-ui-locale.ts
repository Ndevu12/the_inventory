import { create } from "zustand";

import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from "@/i18n/routing";

/**
 * UI locale mirrored for REST calls. DRF resolves ``?language=`` before tenant
 * default; catalog overlays need this plus translated rows in the DB.
 */
type State = { locale: string };

export const useApiUiLocaleStore = create<State>(() => ({
  locale: DEFAULT_LOCALE,
}));

export function getApiUiLocale(): string {
  return useApiUiLocaleStore.getState().locale;
}

export function setApiUiLocale(code: string): void {
  const normalized = SUPPORTED_LOCALES.includes(code) ? code : DEFAULT_LOCALE;
  useApiUiLocaleStore.setState({ locale: normalized });
}
