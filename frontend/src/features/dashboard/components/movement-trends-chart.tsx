"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
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
import type { MovementTrendsData } from "../types/dashboard.types";
import {
  toMovementTrendData,
  formatShortDate,
} from "../helpers/chart-helpers";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

const chartConfig = {
  movements: {
    label: "Movements",
    color: "var(--color-chart-1)",
  },
} satisfies ChartConfig;

interface MovementTrendsChartProps {
  data: MovementTrendsData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

export function MovementTrendsChart({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: MovementTrendsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Movement Trends</CardTitle>
        <CardDescription>Daily stock movements over the last 30 days</CardDescription>
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
          <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <AreaChart data={toMovementTrendData(data)} accessibilityLayer>
              <defs>
                <linearGradient id="movementGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-movements)"
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-movements)"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={formatShortDate}
                interval="preserveStartEnd"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                allowDecimals={false}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={formatShortDate}
                  />
                }
              />
              <Area
                dataKey="movements"
                type="monotone"
                fill="url(#movementGradient)"
                stroke="var(--color-movements)"
                strokeWidth={2}
              />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
