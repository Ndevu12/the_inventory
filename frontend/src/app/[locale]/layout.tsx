import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";

import { LocaleLayoutShell } from "./locale-layout-shell";
import type { MeResponse } from "@/features/auth/types/auth.types";
import { makeQueryClient } from "@/lib/query-client";
import { dehydrateAuthMe, Providers } from "@/lib/providers";
import { JWT_ACCESS_COOKIE_NAME } from "@/lib/auth-paths";
import { fetchAuthMeOnServer } from "@/lib/server/fetch-auth-me";
import { APP_NAME } from "@/lib/utils/constants";
import { localeEntries, routing } from "@/i18n/routing";

function textDirectionForLocale(locale: string): "rtl" | "ltr" {
  const entry = localeEntries.find((e) => e.code === locale);
  return entry?.isRtl ? "rtl" : "ltr";
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "App" });
  return {
    title: APP_NAME,
    description: t("description"),
  };
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages({ locale });
  const dir = textDirectionForLocale(locale);

  const cookieStore = await cookies();
  const hasAccess = cookieStore.get(JWT_ACCESS_COOKIE_NAME)?.value;
  let serverBootstrap: MeResponse | null = null;
  if (hasAccess) {
    const cookieHeader = cookieStore
      .getAll()
      .map((c) => `${c.name}=${c.value}`)
      .join("; ");
    serverBootstrap = await fetchAuthMeOnServer(cookieHeader, locale);
  }

  const queryClient = makeQueryClient();
  const dehydratedState = dehydrateAuthMe(queryClient, serverBootstrap);

  return (
    <Providers
      dehydratedState={dehydratedState}
      serverBootstrap={serverBootstrap}
    >
      <LocaleLayoutShell locale={locale} dir={dir} messages={messages}>
        {children}
      </LocaleLayoutShell>
    </Providers>
  );
}
