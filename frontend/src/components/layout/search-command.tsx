"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "@/i18n/navigation";
import {
  PackageIcon,
  TagsIcon,
  WarehouseIcon,
  TruckIcon,
  UsersIcon,
  ShoppingCartIcon,
  ShoppingBagIcon,
  BarChart3Icon,
  SettingsIcon,
  LayoutDashboardIcon,
  CalendarCheckIcon,
  ScrollTextIcon,
} from "lucide-react";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";

interface SearchRoute {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const SEARCH_ROUTES: { group: string; items: SearchRoute[] }[] = [
  {
    group: "Overview",
    items: [
      { title: "Dashboard", href: "/", icon: LayoutDashboardIcon },
    ],
  },
  {
    group: "Inventory",
    items: [
      { title: "Products", href: "/products", icon: PackageIcon },
      { title: "Categories", href: "/categories", icon: TagsIcon },
      { title: "Stock Locations", href: "/stock/locations", icon: WarehouseIcon },
      { title: "Stock Records", href: "/stock/records", icon: PackageIcon },
      { title: "Stock Movements", href: "/stock/movements", icon: PackageIcon },
      { title: "Stock Lots", href: "/stock/lots", icon: PackageIcon },
    ],
  },
  {
    group: "Orders",
    items: [
      { title: "Reservations", href: "/reservations", icon: CalendarCheckIcon },
      { title: "Cycle Counts", href: "/cycle-counts", icon: CalendarCheckIcon },
    ],
  },
  {
    group: "Procurement",
    items: [
      { title: "Suppliers", href: "/procurement/suppliers", icon: TruckIcon },
      { title: "Purchase Orders", href: "/procurement/purchase-orders", icon: ShoppingCartIcon },
      { title: "Goods Received", href: "/procurement/goods-received", icon: ShoppingCartIcon },
    ],
  },
  {
    group: "Sales",
    items: [
      { title: "Customers", href: "/sales/customers", icon: UsersIcon },
      { title: "Sales Orders", href: "/sales/sales-orders", icon: ShoppingBagIcon },
      { title: "Dispatches", href: "/sales/dispatches", icon: ShoppingBagIcon },
    ],
  },
  {
    group: "Analytics",
    items: [
      { title: "Reports", href: "/reports", icon: BarChart3Icon },
      { title: "Audit Log", href: "/audit-log", icon: ScrollTextIcon },
    ],
  },
  {
    group: "Settings",
    items: [
      { title: "Settings", href: "/settings", icon: SettingsIcon },
      { title: "Team Members", href: "/settings/members", icon: UsersIcon },
    ],
  },
];

interface SearchCommandProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function useSearchCommand() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  return { open, setOpen };
}

export function SearchCommand({ open, onOpenChange }: SearchCommandProps) {
  const router = useRouter();

  const navigate = useCallback(
    (href: string) => {
      onOpenChange?.(false);
      router.push(href);
    },
    [router, onOpenChange],
  );

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <Command>
        <CommandInput placeholder="Search pages..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          {SEARCH_ROUTES.map((group, index) => (
            <div key={group.group}>
              {index > 0 && <CommandSeparator />}
              <CommandGroup heading={group.group}>
                {group.items.map((item) => (
                  <CommandItem
                    key={item.href}
                    onSelect={() => navigate(item.href)}
                  >
                    <item.icon className="mr-2 size-4" />
                    <span>{item.title}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </div>
          ))}
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
