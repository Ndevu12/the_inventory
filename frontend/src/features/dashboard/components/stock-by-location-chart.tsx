"use client";

import { useMemo } from "react";
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
import { useTranslations } from "next-intl";
import type { StockByLocationData } from "../types/dashboard.types";
import { toStockByLocationBarData } from "../helpers/chart-helpers";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

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
  const t = useTranslations("Dashboard");
  const tStock = useTranslations("Dashboard.stockByLocation");
  const genericError = t("error.generic");

  const chartConfig = useMemo(
    () =>
      ({
        reserved: {
          label: tStock("legendReserved"),
          color: "var(--color-chart-4)",
        },
        available: {
          label: tStock("legendAvailable"),
          color: "var(--color-chart-2)",
        },
      }) satisfies ChartConfig,
    [tStock],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{tStock("title")}</CardTitle>
        <CardDescription>{tStock("description")}</CardDescription>
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
        ) : data.labels.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            {tStock("empty")}
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
