import { redirect } from "next/navigation";

import { DEFAULT_LOCALE } from "@/i18n/routing";

/** All app routes live under `[locale]`; send bare `/` to the default locale. */
export default function RootPage() {
  redirect(`/${DEFAULT_LOCALE}`);
}
