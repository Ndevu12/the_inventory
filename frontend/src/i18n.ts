import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";

import { loadMessages } from "./i18n/load-messages";
import { routing } from "./i18n/routing";

/**
 * next-intl request config (Node runtime). Imported only via `next-intl/plugin`.
 *
 * Language list and `routing` live in `./i18n/routing.ts` so middleware and
 * client navigation stay Edge-safe.
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
