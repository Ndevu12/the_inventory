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
import { useAuthStore } from "@/lib/auth-store";

export function TenantSwitcher() {
  const { isMobile } = useSidebar();
  const queryClient = useQueryClient();
  const memberships = useAuthStore((s) => s.memberships);
  const tenantSlug = useAuthStore((s) => s.tenantSlug);
  const setTenant = useAuthStore((s) => s.setTenant);

  const currentTenant = memberships.find(
    (m) => m.tenant__slug === tenantSlug,
  );

  function handleSwitch(slug: string) {
    if (slug === tenantSlug) return;
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
              <span className="truncate font-semibold">
                {currentTenant?.tenant__name ?? "Select Tenant"}
              </span>
              <span className="truncate text-xs text-muted-foreground">
                {currentTenant?.role ?? ""}
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
              <DropdownMenuLabel>Organizations</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {memberships.map((membership) => (
                <DropdownMenuItem
                  key={membership.tenant__slug}
                  onClick={() => handleSwitch(membership.tenant__slug)}
                >
                  <BuildingIcon className="size-4" />
                  <span className="flex-1 truncate">
                    {membership.tenant__name}
                  </span>
                  {membership.tenant__slug === tenantSlug && (
                    <CheckIcon className="ml-auto size-4" />
                  )}
                </DropdownMenuItem>
              ))}
              {memberships.length === 0 && (
                <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                  No organizations found
                </div>
              )}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
