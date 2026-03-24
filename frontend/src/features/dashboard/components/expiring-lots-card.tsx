"use client";

import { AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useLocale, useTranslations } from "next-intl";
import type { ExpiringLotsData, ExpiringLot } from "../types/dashboard.types";
import {
  DashboardWidgetError,
  getDashboardErrorMessage,
} from "./dashboard-widget-error";

interface ExpiringLotsCardProps {
  data: ExpiringLotsData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry?: () => void;
}

function expiryVariant(daysLeft: number | null): "default" | "secondary" | "destructive" | "outline" {
  if (daysLeft === null || daysLeft <= 0) return "destructive";
  if (daysLeft <= 7) return "destructive";
  if (daysLeft <= 14) return "secondary";
  return "outline";
}

function LotRow({ lot }: { lot: ExpiringLot }) {
  const t = useTranslations("Dashboard.expiringLots");
  const locale = useLocale();

  const expiryText =
    lot.days_to_expiry === null
      ? t("expiryUnknown")
      : lot.days_to_expiry <= 0
        ? t("expiryExpired")
        : lot.days_to_expiry === 1
          ? t("expiryOneDay")
          : t("expiryDays", { count: lot.days_to_expiry });

  return (
    <TableRow>
      <TableCell className="font-mono text-xs">{lot.lot_number}</TableCell>
      <TableCell>
        <div>
          <span className="font-medium">{lot.product_name}</span>
          <span className="ml-2 text-xs text-muted-foreground">
            {lot.product_sku}
          </span>
        </div>
      </TableCell>
      <TableCell className="text-right tabular-nums">
        {lot.quantity_remaining.toLocaleString(locale)}
      </TableCell>
      <TableCell className="text-right">
        <Badge variant={expiryVariant(lot.days_to_expiry)}>
          {expiryText}
        </Badge>
      </TableCell>
    </TableRow>
  );
}

export function ExpiringLotsCard({
  data,
  isLoading,
  isError,
  error,
  onRetry,
}: ExpiringLotsCardProps) {
  const t = useTranslations("Dashboard");
  const tLots = useTranslations("Dashboard.expiringLots");
  const genericError = t("error.generic");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="size-5 text-amber-500" />
          {tLots("title")}
        </CardTitle>
        <CardDescription>{tLots("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <DashboardWidgetError
            message={getDashboardErrorMessage(error, genericError)}
            onRetry={onRetry}
            minHeight="200px"
          />
        ) : !data ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data.has_lot_data ? (
          <p className="text-sm text-muted-foreground">
            {tLots("noLotData")}
          </p>
        ) : data.expiring_lots.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {tLots("noExpiring")}
          </p>
        ) : (
          <div className="max-h-[400px] overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{tLots("colLot")}</TableHead>
                  <TableHead>{tLots("colProduct")}</TableHead>
                  <TableHead className="text-right">{tLots("colQty")}</TableHead>
                  <TableHead className="text-right">{tLots("colExpires")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.expiring_lots.map((lot) => (
                  <LotRow key={lot.id} lot={lot} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
