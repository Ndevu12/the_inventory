"use client";

import { useMemo } from "react";
import { Cell, Pie, PieChart } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTranslations } from "next-intl";
import type { OrderStatusData } from "../types/dashboard.types";
import { toPieData, type PieDatum } from "../helpers/chart-helpers";
import { useDashboardStore } from "../stores/dashboard-store";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

const STATUS_KEYS = [
  "Draft",
  "Confirmed",
  "Received",
  "Fulfilled",
  "Cancelled",
] as const;

type StatusKey = (typeof STATUS_KEYS)[number];

const STATUS_COLORS: Record<StatusKey, string> = {
  Draft: "var(--color-chart-1)",
  Confirmed: "var(--color-chart-2)",
  Received: "var(--color-chart-3)",
  Fulfilled: "var(--color-chart-3)",
  Cancelled: "var(--color-chart-4)",
};

const STATUS_KEY_SET = new Set<string>(STATUS_KEYS);

interface OrderStatusChartProps {
  data: OrderStatusData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

function StatusPie({
  items,
  chartConfig,
  emptyLabel,
  totalLabel,
}: {
  items: PieDatum[];
  chartConfig: ChartConfig;
  emptyLabel: string;
  totalLabel: string;
}) {
  const tLabels = useTranslations("Dashboard.orderStatus.statusLabels");

  const displayItems = useMemo(
    () =>
      items.map((d) => ({
        ...d,
        name: STATUS_KEY_SET.has(d.name)
          ? tLabels(d.name as StatusKey)
          : d.name,
      })),
    [items, tLabels],
  );

  const total = displayItems.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-[250px] items-center justify-center text-muted-foreground">
        {emptyLabel}
      </div>
    );
  }

  return (
    <ChartContainer config={chartConfig} className="mx-auto h-[250px] w-full max-w-[300px]">
      <PieChart accessibilityLayer>
        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
        <Pie
          data={displayItems}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={90}
          strokeWidth={2}
          paddingAngle={2}
        >
          {displayItems.map((entry, i) => (
            <Cell key={`${items[i]?.name ?? i}-${i}`} fill={entry.fill} />
          ))}
        </Pie>
        <ChartLegend content={<ChartLegendContent nameKey="name" />} />
        <text
          x="50%"
          y="45%"
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-foreground text-2xl font-bold"
        >
          {total}
        </text>
        <text
          x="50%"
          y="55%"
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-muted-foreground text-xs"
        >
          {totalLabel}
        </text>
      </PieChart>
    </ChartContainer>
  );
}

export function OrderStatusChart({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: OrderStatusChartProps) {
  const { orderChartTab, setOrderChartTab } = useDashboardStore();
  const t = useTranslations("Dashboard");
  const tOrder = useTranslations("Dashboard.orderStatus");
  const tLabels = useTranslations("Dashboard.orderStatus.statusLabels");
  const genericError = t("error.generic");

  const chartConfig = useMemo(() => {
    const cfg: ChartConfig = {};
    for (const key of STATUS_KEYS) {
      const label = tLabels(key);
      cfg[label] = {
        label,
        color: STATUS_COLORS[key],
      };
    }
    return cfg;
  }, [tLabels]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{tOrder("title")}</CardTitle>
        <CardDescription>{tOrder("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : isError ? (
          <DashboardWidgetError
            message={getDashboardErrorMessage(error, genericError)}
            onRetry={onRetry}
            minHeight="300px"
          />
        ) : !data ? (
          <Skeleton className="h-[300px] w-full" />
        ) : (
          <Tabs
            value={orderChartTab}
            onValueChange={(v) =>
              setOrderChartTab(v as "purchase" | "sales")
            }
          >
            <TabsList className="w-full">
              <TabsTrigger value="purchase">{tOrder("tabPurchase")}</TabsTrigger>
              <TabsTrigger value="sales">{tOrder("tabSales")}</TabsTrigger>
            </TabsList>
            <TabsContent value="purchase">
              <StatusPie
                items={toPieData(data.purchase_orders)}
                chartConfig={chartConfig}
                emptyLabel={tOrder("empty")}
                totalLabel={tOrder("totalLabel")}
              />
            </TabsContent>
            <TabsContent value="sales">
              <StatusPie
                items={toPieData(data.sales_orders)}
                chartConfig={chartConfig}
                emptyLabel={tOrder("empty")}
                totalLabel={tOrder("totalLabel")}
              />
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
