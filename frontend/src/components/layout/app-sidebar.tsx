"use client";

import { Link, usePathname } from "@/i18n/navigation";
import { useAuth } from "@/features/auth/context/auth-context";
import {
  LayoutDashboardIcon,
  PackageIcon,
  TagsIcon,
  Building2Icon,
  MapPinIcon,
  DatabaseIcon,
  ArrowRightLeftIcon,
  BoxesIcon,
  CalendarCheckIcon,
  ClipboardListIcon,
  LayersIcon,
  TruckIcon,
  ShoppingCartIcon,
  ReceiptIcon,
  UsersIcon,
  ShoppingBagIcon,
  PackageCheckIcon,
  BarChart3Icon,
  ScrollTextIcon,
  SettingsIcon,
  UsersRoundIcon,
  UserCogIcon,
  CreditCardIcon,
  MailIcon,
  UserIcon,
  type LucideIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { TenantSwitcher } from "./tenant-switcher";
import { UserMenu } from "./user-menu";

type NavItemDef = {
  itemKey: string;
  href: string;
  icon: LucideIcon;
};

type NavGroupDef = {
  groupKey: string;
  items: NavItemDef[];
  platformItems?: NavItemDef[];
};

const NAV_GROUPS: NavGroupDef[] = [
  {
    groupKey: "overview",
    items: [
      { itemKey: "dashboard", href: "/", icon: LayoutDashboardIcon },
    ],
  },
  {
    groupKey: "inventory",
    items: [
      { itemKey: "products", href: "/products", icon: PackageIcon },
      { itemKey: "categories", href: "/categories", icon: TagsIcon },
    ],
  },
  {
    groupKey: "stock",
    items: [
      { itemKey: "warehouses", href: "/stock/warehouses", icon: Building2Icon },
      { itemKey: "stockLocations", href: "/stock/locations", icon: MapPinIcon },
      { itemKey: "stockRecords", href: "/stock/records", icon: DatabaseIcon },
      { itemKey: "stockMovements", href: "/stock/movements", icon: ArrowRightLeftIcon },
      { itemKey: "stockLots", href: "/stock/lots", icon: BoxesIcon },
    ],
  },
  {
    groupKey: "orders",
    items: [
      { itemKey: "reservations", href: "/reservations", icon: CalendarCheckIcon },
      { itemKey: "cycleCounts", href: "/cycle-counts", icon: ClipboardListIcon },
      { itemKey: "bulkOperations", href: "/bulk-operations", icon: LayersIcon },
    ],
  },
  {
    groupKey: "procurement",
    items: [
      { itemKey: "suppliers", href: "/procurement/suppliers", icon: TruckIcon },
      { itemKey: "purchaseOrders", href: "/procurement/purchase-orders", icon: ShoppingCartIcon },
      { itemKey: "goodsReceived", href: "/procurement/goods-received", icon: ReceiptIcon },
    ],
  },
  {
    groupKey: "sales",
    items: [
      { itemKey: "customers", href: "/sales/customers", icon: UsersIcon },
      { itemKey: "salesOrders", href: "/sales/sales-orders", icon: ShoppingBagIcon },
      { itemKey: "dispatches", href: "/sales/dispatches", icon: PackageCheckIcon },
    ],
  },
  {
    groupKey: "analytics",
    items: [
      { itemKey: "reports", href: "/reports", icon: BarChart3Icon },
      { itemKey: "auditLog", href: "/audit-log", icon: ScrollTextIcon },
    ],
    platformItems: [
      { itemKey: "platformAuditLog", href: "/settings/platform-audit-log", icon: ScrollTextIcon },
    ],
  },
  {
    groupKey: "settings",
    items: [
      { itemKey: "account", href: "/settings/profile", icon: UserIcon },
      { itemKey: "tenant", href: "/settings", icon: SettingsIcon },
      { itemKey: "teamMembers", href: "/settings/members", icon: UsersRoundIcon },
    ],
    platformItems: [
      { itemKey: "platformUsers", href: "/settings/users", icon: UserCogIcon },
      { itemKey: "invitations", href: "/settings/invitations", icon: MailIcon },
      { itemKey: "billing", href: "/settings/billing", icon: CreditCardIcon },
    ],
  },
];

function isActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/settings") return pathname === "/settings";
  return pathname === href || pathname.startsWith(href + "/");
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const { user } = useAuth();
  const isSuperuser = !!user?.is_superuser;
  const t = useTranslations("Nav");

  const getGroupItems = (group: NavGroupDef) => {
    const items = [...group.items];
    if (isSuperuser && group.platformItems?.length) {
      items.push(...group.platformItems);
    }
    return items;
  };

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TenantSwitcher />
      </SidebarHeader>
      <SidebarContent>
        {NAV_GROUPS.map((group) => (
          <SidebarGroup key={group.groupKey}>
            <SidebarGroupLabel>
              {t(`groups.${group.groupKey}`)}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {getGroupItems(group).map((item) => {
                  const title = t(`items.${item.itemKey}`);
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton
                        render={<Link href={item.href} />}
                        tooltip={title}
                        isActive={isActive(item.href, pathname)}
                      >
                        <item.icon />
                        <span>{title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
