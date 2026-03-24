"use client";

import type { AbstractIntlMessages } from "next-intl";
import { NextIntlClientProvider } from "next-intl";
import { useEffect } from "react";

import { TenantLocaleSync } from "@/components/tenant-locale-sync";

export function LocaleLayoutShell({
  locale,
  dir,
  messages,
  children,
}: {
  locale: string;
  dir: "rtl" | "ltr";
  messages: AbstractIntlMessages;
  children: React.ReactNode;
}) {
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
  }, [locale, dir]);

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <TenantLocaleSync />
      {children}
    </NextIntlClientProvider>
  );
}
