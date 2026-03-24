"use client";

import type { AbstractIntlMessages } from "next-intl";
import { NextIntlClientProvider } from "next-intl";
import { useEffect, useLayoutEffect } from "react";

import { TenantLocaleSync } from "@/components/tenant-locale-sync";
import { setApiUiLocale } from "@/lib/api-ui-locale";

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
  useLayoutEffect(() => {
    setApiUiLocale(locale);
  }, [locale]);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
  }, [locale, dir]);

  return (
    <NextIntlClientProvider
      key={locale}
      locale={locale}
      messages={messages}
    >
      <TenantLocaleSync />
      {children}
    </NextIntlClientProvider>
  );
}
