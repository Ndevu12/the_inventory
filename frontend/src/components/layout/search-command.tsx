"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "@/i18n/navigation";
import { useAllLocations } from "@/features/inventory/hooks/use-locations";
import {
  PackageIcon,
  TagsIcon,
  WarehouseIcon,
  TruckIcon,
  UsersIcon,
  ShoppingCartIcon,
  ShoppingBagIcon,
  PackageCheckIcon,
  ReceiptIcon,
  UsersRoundIcon,
  BarChart3Icon,
  SettingsIcon,
  LayoutDashboardIcon,
  CalendarCheckIcon,
  ClipboardListIcon,
  ScrollTextIcon,
  DatabaseIcon,
  ArrowRightLeftIcon,
  BoxesIcon,
  type LucideIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
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

type SearchNavItem = {
  itemKey: string;
  href: string;
  icon: LucideIcon;
};

type SearchNavGroup = {
  groupKey: string;
  items: SearchNavItem[];
};

/** Same `Nav` message keys and routes as the sidebar subset exposed in the palette. */
const SEARCH_NAV_GROUPS: SearchNavGroup[] = [
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
      { itemKey: "stockLocations", href: "/stock/locations", icon: WarehouseIcon },
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
  },
  {
    groupKey: "settings",
    items: [
      { itemKey: "tenant", href: "/settings", icon: SettingsIcon },
      { itemKey: "teamMembers", href: "/settings/members", icon: UsersRoundIcon },
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
  const pathname = usePathname();
  const tNav = useTranslations("Nav");
  const tCommon = useTranslations("Common");
  const tInv = useTranslations("Inventory");

  const { data: jumpLocations = [] } = useAllLocations({ enabled: open });

  const navigate = useCallback(
    (href: string) => {
      onOpenChange?.(false);
      router.push(href);
    },
    [router, onOpenChange],
  );

  const navigateToLocation = useCallback(
    (locationId: number) => {
      onOpenChange?.(false);
      if (pathname.includes("/stock/locations")) {
        const q = new URLSearchParams();
        q.set("focus", String(locationId));
        router.push(`${pathname}?${q.toString()}`);
      } else {
        router.push(`/stock/locations?focus=${locationId}`);
      }
    },
    [onOpenChange, pathname, router],
  );

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <Command>
        <CommandInput placeholder={tCommon("commandSearchPlaceholder")} />
        <CommandList>
          <CommandEmpty>{tCommon("noResults")}</CommandEmpty>
          {SEARCH_NAV_GROUPS.map((group, index) => (
            <div key={group.groupKey}>
              {index > 0 && <CommandSeparator />}
              <CommandGroup heading={tNav(`groups.${group.groupKey}`)}>
                {group.items.map((item) => (
                  <CommandItem
                    key={item.href}
                    onSelect={() => navigate(item.href)}
                  >
                    <item.icon className="mr-2 size-4" />
                    <span>{tNav(`items.${item.itemKey}`)}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </div>
          ))}
          {jumpLocations.length > 0 ? (
            <>
              <CommandSeparator />
              <CommandGroup
                heading={tInv("locations.commandPalette.groupHeading")}
              >
                {jumpLocations.map((loc) => (
                  <CommandItem
                    key={loc.id}
                    value={`${loc.name} ${loc.id} ${loc.materialized_path ?? ""} ${loc.warehouse?.name ?? ""}`}
                    onSelect={() => navigateToLocation(loc.id)}
                  >
                    <WarehouseIcon className="mr-2 size-4" />
                    <span className="truncate">{loc.name}</span>
                    {loc.warehouse?.name ? (
                      <span className="ml-1 truncate text-xs text-muted-foreground">
                        {loc.warehouse.name}
                      </span>
                    ) : null}
                  </CommandItem>
                ))}
              </CommandGroup>
            </>
          ) : null}
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
