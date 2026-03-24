"use client";

import { Languages } from "lucide-react";
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
import type { AppLocale } from "@/i18n/routing";
import { routing } from "@/i18n/routing";
import { persistLocalePreference } from "@/lib/locale-preference";

export function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations("LanguageSwitcher");
  const tLang = useTranslations("LanguageSwitcher.languages");
  const router = useRouter();
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
            router.replace(pathname, { locale: next });
          }}
        >
          {routing.locales.map((code) => (
            <DropdownMenuRadioItem key={code} value={code}>
              {tLang(code as AppLocale)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
