"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
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
import type { StockByLocationData } from "../types/dashboard.types";
import { toStockByLocationBarData } from "../helpers/chart-helpers";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

const chartConfig = {
  reserved: {
    label: "Reserved",
    color: "var(--color-chart-4)",
  },
  available: {
    label: "Available",
    color: "var(--color-chart-2)",
  },
} satisfies ChartConfig;

interface StockByLocationChartProps {
  data: StockByLocationData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

export function StockByLocationChart({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: StockByLocationChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Stock by Location</CardTitle>
        <CardDescription>
          Available and reserved quantities per location
        </CardDescription>
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
        ) : data.labels.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            No stock data available
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <BarChart
              data={toStockByLocationBarData(data)}
              accessibilityLayer
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="name"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(v: string) =>
                  v.length > 12 ? `${v.slice(0, 12)}…` : v
                }
              />
              <YAxis tickLine={false} axisLine={false} tickMargin={8} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar
                dataKey="available"
                stackId="stock"
                fill="var(--color-available)"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="reserved"
                stackId="stock"
                fill="var(--color-reserved)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
