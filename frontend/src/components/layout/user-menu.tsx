"use client";

import { useRouter } from "@/i18n/navigation";
import { LogOutIcon, UserIcon, ChevronsUpDownIcon, UserXIcon } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import { useAuth } from "@/features/auth/context/auth-context";
import { useLogout, useExitImpersonation } from "@/features/auth/hooks/use-auth";
import { useTranslations } from "next-intl";

export function UserMenu() {
  const t = useTranslations("Shell");
  const router = useRouter();
  const { isMobile } = useSidebar();
  const { user, memberships, tenantSlug, isImpersonating } = useAuth();
  const handleLogout = useLogout();
  const exitImpersonation = useExitImpersonation();

  const currentMembership = memberships.find(
    (m) => m.tenant__slug === tenantSlug,
  );
  const displayName = user
    ? `${user.first_name} ${user.last_name}`.trim() || user.username
    : t("userFallback");
  const initials = user
    ? (user.first_name?.[0] ?? "") + (user.last_name?.[0] ?? "") ||
      user.username[0]?.toUpperCase()
    : "U";

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
            <Avatar size="sm" className="size-8 rounded-lg">
              <AvatarFallback className="rounded-lg text-xs">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{displayName}</span>
              <span className="truncate text-xs text-muted-foreground">
                {currentMembership?.role ?? t("memberFallback")}
              </span>
            </div>
            <ChevronsUpDownIcon className="ml-auto size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-56"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium">{displayName}</p>
                  <p className="text-xs text-muted-foreground">
                    {user?.email ?? ""}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/settings/profile")}>
                <UserIcon />
                {t("profileAccount")}
              </DropdownMenuItem>
              {isImpersonating && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => exitImpersonation.mutate()}
                    disabled={exitImpersonation.isPending}
                  >
                    <UserXIcon />
                    {t("exitImpersonation")}
                  </DropdownMenuItem>
                </>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleLogout()}>
                <LogOutIcon />
                {t("logOut")}
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
