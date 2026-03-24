"use client";

import { SearchIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "./breadcrumbs";
import { ThemeToggle } from "./theme-toggle";
import { SearchCommand, useSearchCommand } from "./search-command";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export function Header() {
  const t = useTranslations("Common");
  const { open: searchOpen, setOpen: setSearchOpen } = useSearchCommand();

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex flex-1 items-center gap-2">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumbs />
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setSearchOpen(true)}
          aria-label={t("searchAria")}
          className="sm:hidden"
        >
          <SearchIcon className="size-4" />
        </Button>
        <Button
          variant="outline"
          className="hidden h-8 w-48 justify-start text-sm text-muted-foreground sm:inline-flex"
          onClick={() => setSearchOpen(true)}
        >
          <SearchIcon className="mr-2 size-4" />
          {t("searchPlaceholder")}
          <kbd className="pointer-events-none ml-auto inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <span className="text-xs">⌘</span>K
          </kbd>
        </Button>
        <LanguageSwitcher />
        <ThemeToggle />
      </div>

      <SearchCommand open={searchOpen} onOpenChange={setSearchOpen} />
    </header>
  );
}
