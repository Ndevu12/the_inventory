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
import type { ExpiringLotsData, ExpiringLot } from "../types/dashboard.types";

interface ExpiringLotsCardProps {
  data: ExpiringLotsData | undefined;
  isLoading: boolean;
}

function expiryVariant(daysLeft: number | null): "default" | "secondary" | "destructive" | "outline" {
  if (daysLeft === null || daysLeft <= 0) return "destructive";
  if (daysLeft <= 7) return "destructive";
  if (daysLeft <= 14) return "secondary";
  return "outline";
}

function expiryLabel(daysLeft: number | null): string {
  if (daysLeft === null) return "Unknown";
  if (daysLeft <= 0) return "Expired";
  if (daysLeft === 1) return "1 day";
  return `${daysLeft} days`;
}

function LotRow({ lot }: { lot: ExpiringLot }) {
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
        {lot.quantity_remaining.toLocaleString()}
      </TableCell>
      <TableCell className="text-right">
        <Badge variant={expiryVariant(lot.days_to_expiry)}>
          {expiryLabel(lot.days_to_expiry)}
        </Badge>
      </TableCell>
    </TableRow>
  );
}

export function ExpiringLotsCard({ data, isLoading }: ExpiringLotsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="size-5 text-amber-500" />
          Expiring Lots
        </CardTitle>
        <CardDescription>Lots expiring within the next 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading || !data ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data.has_lot_data ? (
          <p className="text-sm text-muted-foreground">
            No lot tracking data available
          </p>
        ) : data.expiring_lots.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No lots expiring in the next 30 days
          </p>
        ) : (
          <div className="max-h-[400px] overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Lot #</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Expires</TableHead>
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
