"use client";

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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardSummary } from "../types/dashboard.types";
import { formatCompactNumber, formatCurrency } from "../helpers/chart-helpers";

interface KpiCardsProps {
  data: DashboardSummary | undefined;
  isLoading: boolean;
}

interface KpiItem {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

function buildKpis(data: DashboardSummary): KpiItem[] {
  return [
    {
      title: "Total Products",
      value: formatCompactNumber(data.total_products),
      icon: Package,
      description: "Active products in catalogue",
    },
    {
      title: "Locations",
      value: formatCompactNumber(data.total_locations),
      icon: MapPin,
      description: "Active stock locations",
    },
    {
      title: "Low Stock",
      value: formatCompactNumber(data.low_stock_count),
      icon: AlertTriangle,
      description: "Products below reorder point",
    },
    {
      title: "Reserved",
      value: formatCompactNumber(data.total_reserved),
      icon: ShieldCheck,
      description: `${formatCompactNumber(data.total_available)} available`,
    },
    {
      title: "Purchase Orders",
      value: formatCompactNumber(data.purchase_orders),
      icon: ShoppingCart,
      description: "Total purchase orders",
    },
    {
      title: "Sales Orders",
      value: formatCompactNumber(data.sales_orders),
      icon: Truck,
      description: "Total sales orders",
    },
    {
      title: "Reserved Value",
      value: formatCurrency(data.reserved_stock_value),
      icon: DollarSign,
      description: "Value of reserved stock",
    },
    {
      title: "Stock Records",
      value: formatCompactNumber(data.total_stock_records),
      icon: Layers,
      description: "Product-location records",
    },
  ];
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

export function KpiCards({ data, isLoading }: KpiCardsProps) {
  if (isLoading || !data) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <KpiSkeleton key={i} />
        ))}
      </div>
    );
  }

  const kpis = buildKpis(data);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.title} size="sm">
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
