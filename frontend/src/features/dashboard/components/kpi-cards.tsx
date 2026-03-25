"use client";

import { useMemo } from "react";
import {
  Package,
  MapPin,
  AlertTriangle,
  ShieldCheck,
  ShoppingCart,
  Truck,
  DollarSign,
  Layers,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardSummary } from "../types/dashboard.types";
import { formatCompactNumber, formatCurrency } from "../helpers/chart-helpers";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

interface KpiCardsProps {
  data: DashboardSummary | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

interface KpiItem {
  id: string;
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

function KpiSkeleton() {
  return (
    <Card size="sm">
      <CardHeader className="flex flex-row items-center justify-between pb-1">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="mb-1 h-7 w-20" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

export function KpiCards({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: KpiCardsProps) {
  const t = useTranslations("Dashboard");
  const locale = useLocale();
  const genericError = t("error.generic");

  const kpis = useMemo((): KpiItem[] | null => {
    if (!data) return null;
    return [
      {
        id: "totalProducts",
        title: t("kpi.totalProducts.title"),
        value: formatCompactNumber(data.total_products, locale),
        icon: Package,
        description: t("kpi.totalProducts.description"),
      },
      {
        id: "locations",
        title: t("kpi.locations.title"),
        value: formatCompactNumber(data.total_locations, locale),
        icon: MapPin,
        description: t("kpi.locations.description", {
          facilities: formatCompactNumber(data.active_warehouses, locale),
          retail: formatCompactNumber(data.locations_retail_site, locale),
          linked: formatCompactNumber(data.locations_with_warehouse, locale),
        }),
      },
      {
        id: "lowStock",
        title: t("kpi.lowStock.title"),
        value: formatCompactNumber(data.low_stock_count, locale),
        icon: AlertTriangle,
        description: t("kpi.lowStock.description"),
      },
      {
        id: "reserved",
        title: t("kpi.reserved.title"),
        value: formatCompactNumber(data.total_reserved, locale),
        icon: ShieldCheck,
        description: t("kpi.reserved.description", {
          available: formatCompactNumber(data.total_available, locale),
        }),
      },
      {
        id: "purchaseOrders",
        title: t("kpi.purchaseOrders.title"),
        value: formatCompactNumber(data.purchase_orders, locale),
        icon: ShoppingCart,
        description: t("kpi.purchaseOrders.description"),
      },
      {
        id: "salesOrders",
        title: t("kpi.salesOrders.title"),
        value: formatCompactNumber(data.sales_orders, locale),
        icon: Truck,
        description: t("kpi.salesOrders.description"),
      },
      {
        id: "reservedValue",
        title: t("kpi.reservedValue.title"),
        value: formatCurrency(data.reserved_stock_value, locale),
        icon: DollarSign,
        description: t("kpi.reservedValue.description"),
      },
      {
        id: "stockRecords",
        title: t("kpi.stockRecords.title"),
        value: formatCompactNumber(data.total_stock_records, locale),
        icon: Layers,
        description: t("kpi.stockRecords.description"),
      },
    ];
  }, [data, locale, t]);

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <KpiSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2 lg:col-span-4">
          <DashboardWidgetError
            message={getDashboardErrorMessage(error, genericError)}
            onRetry={onRetry}
            minHeight="160px"
          />
        </div>
      </div>
    );
  }

  if (!data || !kpis) {
    return null;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.id} size="sm">
          <CardHeader className="flex flex-row items-center justify-between pb-1">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {kpi.title}
            </CardTitle>
            <kpi.icon className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpi.value}</div>
            <p className="text-xs text-muted-foreground">{kpi.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
