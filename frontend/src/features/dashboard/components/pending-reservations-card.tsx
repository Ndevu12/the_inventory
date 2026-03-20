"use client";

import { ShieldCheck, Clock, CheckCircle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import type { PendingReservationsData } from "../types/dashboard.types";
import { formatCompactNumber, formatCurrency } from "../helpers/chart-helpers";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

interface PendingReservationsCardProps {
  data: PendingReservationsData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

export function PendingReservationsCard({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: PendingReservationsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-5" />
          Pending Reservations
        </CardTitle>
        <CardDescription>Active reservation summary</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        ) : isError ? (
          <DashboardWidgetError
            message={getDashboardErrorMessage(error)}
            onRetry={onRetry}
            minHeight="140px"
          />
        ) : !data ? (
          <div className="space-y-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        ) : data.reservation_count === 0 ? (
          <p className="text-sm text-muted-foreground">
            No active reservations
          </p>
        ) : (
          <div className="space-y-4">
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-bold">
                {formatCompactNumber(data.reservation_count)}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatCompactNumber(data.total_units)} units ·{" "}
                {formatCurrency(data.total_value)}
              </span>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-md border p-3">
                <div className="flex items-center gap-2">
                  <Clock className="size-4 text-amber-500" />
                  <span className="text-sm font-medium">Pending</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {data.pending.count} orders
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {formatCompactNumber(data.pending.units)} units
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-md border p-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="size-4 text-green-500" />
                  <span className="text-sm font-medium">Confirmed</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {data.confirmed.count} orders
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {formatCompactNumber(data.confirmed.units)} units
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
