"use client";

import { Languages } from "lucide-react";
import { useRouter as useNextRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { usePathname, useRouter } from "@/i18n/navigation";
import { localeEntries, routing } from "@/i18n/routing";
import { setApiUiLocale } from "@/lib/api-ui-locale";
import { persistLocalePreference } from "@/lib/locale-preference";

function displayNameForLocale(code: string): string {
  return localeEntries.find((e) => e.code === code)?.displayName ?? code;
}

export function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations("LanguageSwitcher");
  const router = useRouter();
  const refresh = useNextRouter().refresh;
  const pathname = usePathname();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("ariaLabel")}
            className="shrink-0"
          />
        }
      >
        <Languages className="size-4" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[10rem]">
        <DropdownMenuRadioGroup
          value={locale}
          onValueChange={(next) => {
            if (next === locale) return;
            persistLocalePreference(next);
            setApiUiLocale(next);
            router.replace(pathname, { locale: next });
            refresh();
          }}
        >
          {routing.locales.map((code) => (
            <DropdownMenuRadioItem key={code} value={code}>
              {displayNameForLocale(code)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
