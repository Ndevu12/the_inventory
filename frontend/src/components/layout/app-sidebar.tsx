"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/context/auth-context";
import {
  LayoutDashboardIcon,
  PackageIcon,
  TagsIcon,
  WarehouseIcon,
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
  type LucideIcon,
} from "lucide-react";
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

interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  items: NavItem[];
  platformItems?: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { title: "Dashboard", href: "/", icon: LayoutDashboardIcon },
    ],
  },
  {
    label: "Inventory",
    items: [
      { title: "Products", href: "/products", icon: PackageIcon },
      { title: "Categories", href: "/categories", icon: TagsIcon },
      { title: "Stock Locations", href: "/stock/locations", icon: WarehouseIcon },
      { title: "Stock Records", href: "/stock/records", icon: DatabaseIcon },
      { title: "Stock Movements", href: "/stock/movements", icon: ArrowRightLeftIcon },
      { title: "Stock Lots", href: "/stock/lots", icon: BoxesIcon },
    ],
  },
  {
    label: "Orders",
    items: [
      { title: "Reservations", href: "/reservations", icon: CalendarCheckIcon },
      { title: "Cycle Counts", href: "/cycle-counts", icon: ClipboardListIcon },
      { title: "Bulk Operations", href: "/bulk-operations", icon: LayersIcon },
    ],
  },
  {
    label: "Procurement",
    items: [
      { title: "Suppliers", href: "/procurement/suppliers", icon: TruckIcon },
      { title: "Purchase Orders", href: "/procurement/purchase-orders", icon: ShoppingCartIcon },
      { title: "Goods Received", href: "/procurement/goods-received", icon: ReceiptIcon },
    ],
  },
  {
    label: "Sales",
    items: [
      { title: "Customers", href: "/sales/customers", icon: UsersIcon },
      { title: "Sales Orders", href: "/sales/sales-orders", icon: ShoppingBagIcon },
      { title: "Dispatches", href: "/sales/dispatches", icon: PackageCheckIcon },
    ],
  },
  {
    label: "Analytics",
    items: [
      { title: "Reports", href: "/reports", icon: BarChart3Icon },
      { title: "Audit Log", href: "/audit-log", icon: ScrollTextIcon },
    ],
    platformItems: [
      { title: "Platform Audit Log", href: "/settings/platform-audit-log", icon: ScrollTextIcon },
    ],
  },
  {
    label: "Settings",
    items: [
      { title: "Tenant", href: "/settings", icon: SettingsIcon },
      { title: "Team Members", href: "/settings/members", icon: UsersRoundIcon },
    ],
    /** Superuser-only item; appended when user.is_superuser */
    platformItems: [
      { title: "Users", href: "/settings/users", icon: UserCogIcon },
      { title: "Invitations", href: "/settings/invitations", icon: MailIcon },
      { title: "Billing", href: "/settings/billing", icon: CreditCardIcon },
    ],
  },
];

function isActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const { user } = useAuth();
  const isSuperuser = !!user?.is_superuser;

  const getGroupItems = (group: NavGroup) => {
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
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {getGroupItems(group).map((item) => (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      render={<Link href={item.href} />}
                      tooltip={item.title}
                      isActive={isActive(item.href, pathname)}
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
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
