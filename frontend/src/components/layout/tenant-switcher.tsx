"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ChevronsUpDownIcon, BuildingIcon, CheckIcon } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useMe } from "@/features/auth/hooks/use-auth";
import { useAuthStore } from "@/lib/auth-store";
import { useTranslations } from "next-intl";

export function TenantSwitcher() {
  const t = useTranslations("Shell");
  const { isMobile } = useSidebar();
  const queryClient = useQueryClient();
  const memberships = useAuthStore((s) => s.memberships);
  const tenantSlug = useAuthStore((s) => s.tenantSlug);
  const accessToken = useAuthStore((s) => s.accessToken);
  const setTenant = useAuthStore((s) => s.setTenant);

  const { data: meData, isPending, isFetching } = useMe();

  const effectiveSlug = tenantSlug ?? meData?.tenant?.slug ?? null;
  const orgList =
    memberships.length > 0 ? memberships : (meData?.memberships ?? []);
  const currentRow = effectiveSlug
    ? orgList.find((m) => m.tenant__slug === effectiveSlug)
    : undefined;

  const bootstrapping =
    !!accessToken && orgList.length === 0 && (isPending || isFetching);

  const displayName = bootstrapping
    ? t("tenantLoading")
    : (currentRow?.tenant__name ??
        (meData?.tenant &&
        (!effectiveSlug || meData.tenant.slug === effectiveSlug)
          ? meData.tenant.name
          : null) ??
        t("selectTenant"));

  const roleLabel =
    currentRow?.role ?? meData?.tenant?.role ?? "";

  function handleSwitch(slug: string) {
    if (slug === effectiveSlug) return;
    setTenant(slug);
    queryClient.invalidateQueries();
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton
                size="lg"
                className="data-open:bg-sidebar-accent data-open:text-sidebar-accent-foreground"
              />
            }
          >
            <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <BuildingIcon className="size-4" />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-semibold">{displayName}</span>
              <span className="truncate text-xs text-muted-foreground">
                {roleLabel}
              </span>
            </div>
            <ChevronsUpDownIcon className="ml-auto size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-64"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel>{t("organizations")}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {bootstrapping && (
                <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                  {t("loadingOrganizations")}
                </div>
              )}
              {!bootstrapping &&
                orgList.map((membership) => (
                  <DropdownMenuItem
                    key={membership.tenant__slug}
                    onClick={() => handleSwitch(membership.tenant__slug)}
                  >
                    <BuildingIcon className="size-4" />
                    <span className="flex-1 truncate">
                      {membership.tenant__name}
                    </span>
                    {membership.tenant__slug === effectiveSlug && (
                      <CheckIcon className="ml-auto size-4" />
                    )}
                  </DropdownMenuItem>
                ))}
              {!bootstrapping && orgList.length === 0 && (
                <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                  {t("noOrganizations")}
                </div>
              )}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
