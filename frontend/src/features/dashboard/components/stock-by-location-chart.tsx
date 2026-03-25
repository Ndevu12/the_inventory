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
import { useLocale, useTranslations } from "next-intl";
import type { StockByLocationData } from "../types/dashboard.types";
import {
  formatCompactNumber,
  toStockByLocationBarData,
} from "../helpers/chart-helpers";
import { Badge } from "@/components/ui/badge";
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
  const locale = useLocale();
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
                  v.length > 18 ? `${v.slice(0, 18)}…` : v
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
        {!isLoading && !isError && data && data.by_site.length > 0 ? (
          <div className="mt-6 border-t pt-4">
            <h3 className="mb-3 text-sm font-medium">{tStock("bySiteTitle")}</h3>
            <p className="mb-3 text-xs text-muted-foreground">
              {tStock("bySiteHint")}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-2 font-medium">{tStock("colSite")}</th>
                    <th className="pb-2 pr-2 font-medium">{tStock("colKind")}</th>
                    <th className="pb-2 pr-2 text-right font-medium tabular-nums">
                      {tStock("colTotal")}
                    </th>
                    <th className="pb-2 pr-2 text-right font-medium tabular-nums">
                      {tStock("colReserved")}
                    </th>
                    <th className="pb-2 text-right font-medium tabular-nums">
                      {tStock("colAvailable")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.by_site.map((row) => (
                    <tr key={String(row.warehouse_id)} className="border-b last:border-0">
                      <td className="py-2 pr-2">{row.label}</td>
                      <td className="py-2 pr-2">
                        <Badge variant="secondary" className="text-xs font-normal">
                          {row.kind === "warehouse"
                            ? tStock("kindWarehouse")
                            : tStock("kindRetail")}
                        </Badge>
                      </td>
                      <td className="py-2 pr-2 text-right tabular-nums">
                        {formatCompactNumber(row.total_quantity, locale)}
                      </td>
                      <td className="py-2 pr-2 text-right tabular-nums">
                        {formatCompactNumber(row.reserved, locale)}
                      </td>
                      <td className="py-2 text-right tabular-nums">
                        {formatCompactNumber(row.available, locale)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
