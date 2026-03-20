"use client";

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
import type { OrderStatusData } from "../types/dashboard.types";
import { toPieData, type PieDatum } from "../helpers/chart-helpers";
import { useDashboardStore } from "../stores/dashboard-store";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

const chartConfig = {
  Draft: { label: "Draft", color: "var(--color-chart-1)" },
  Confirmed: { label: "Confirmed", color: "var(--color-chart-2)" },
  Received: { label: "Received", color: "var(--color-chart-3)" },
  Fulfilled: { label: "Fulfilled", color: "var(--color-chart-3)" },
  Cancelled: { label: "Cancelled", color: "var(--color-chart-4)" },
} satisfies ChartConfig;

interface OrderStatusChartProps {
  data: OrderStatusData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

function StatusPie({ items }: { items: PieDatum[] }) {
  const total = items.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-[250px] items-center justify-center text-muted-foreground">
        No orders yet
      </div>
    );
  }

  return (
    <ChartContainer config={chartConfig} className="mx-auto h-[250px] w-full max-w-[300px]">
      <PieChart accessibilityLayer>
        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
        <Pie
          data={items}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={90}
          strokeWidth={2}
          paddingAngle={2}
        >
          {items.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
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
          Total
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Order Status</CardTitle>
        <CardDescription>Distribution by current status</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : isError ? (
          <DashboardWidgetError
            message={getDashboardErrorMessage(error)}
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
              <TabsTrigger value="purchase">Purchase Orders</TabsTrigger>
              <TabsTrigger value="sales">Sales Orders</TabsTrigger>
            </TabsList>
            <TabsContent value="purchase">
              <StatusPie items={toPieData(data.purchase_orders)} />
            </TabsContent>
            <TabsContent value="sales">
              <StatusPie items={toPieData(data.sales_orders)} />
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
