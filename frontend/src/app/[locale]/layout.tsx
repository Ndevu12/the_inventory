import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";

import { LocaleLayoutShell } from "./locale-layout-shell";
import { Providers } from "@/lib/providers";
import { APP_NAME } from "@/lib/utils/constants";
import { routing } from "@/i18n/routing";

const RTL_LOCALES = new Set<string>(["ar"]);

function textDirectionForLocale(locale: string): "rtl" | "ltr" {
  return RTL_LOCALES.has(locale) ? "rtl" : "ltr";
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
  const messages = await getMessages();
  const dir = textDirectionForLocale(locale);

  return (
    <Providers>
      <LocaleLayoutShell locale={locale} dir={dir} messages={messages}>
        {children}
      </LocaleLayoutShell>
    </Providers>
  );
}
