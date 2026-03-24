import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";

import { loadMessages } from "./i18n/load-messages";
import { routing } from "./i18n/routing";

/**
 * next-intl request config (Node runtime). Imported only via `next-intl/plugin`.
 *
 * Locale codes are bundled from `./i18n/locales-config.json` (run Django
 * ``sync_frontend_locales`` after Wagtail locale changes).
 */
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  const messages = await loadMessages(locale);

  return {
    locale,
    messages,
  };
});
