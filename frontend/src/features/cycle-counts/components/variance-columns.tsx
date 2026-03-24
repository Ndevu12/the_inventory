"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  InventoryVariance,
  VarianceResolution,
  VarianceType,
} from "../types/cycle-count.types";
import {
  VARIANCE_TYPE_COLOR_MAP,
  RESOLUTION_COLOR_MAP,
} from "../helpers/cycle-constants";

export function getVarianceColumns(
  tCol: (key: string) => string,
  tType: (key: string) => string,
  tResolution: (key: string) => string,
): ColumnDef<InventoryVariance, unknown>[] {
  return [
    {
      accessorKey: "product_name",
      header: tCol("product"),
      cell: ({ row }) => (
        <div>
          <span className="font-medium">{row.original.product_name}</span>
          <span className="ml-2 text-xs text-muted-foreground">
            {row.original.product_sku}
          </span>
        </div>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "location_name",
      header: tCol("location"),
      enableSorting: false,
    },
    {
      accessorKey: "system_quantity",
      header: tCol("systemQty"),
    },
    {
      accessorKey: "physical_quantity",
      header: tCol("physicalQty"),
    },
    {
      accessorKey: "variance_quantity",
      header: tCol("variance"),
      cell: ({ row }) => {
        const qty = row.original.variance_quantity;
        return (
          <span
            className={cn(
              "font-medium",
              qty > 0 && "text-blue-600 dark:text-blue-400",
              qty < 0 && "text-red-600 dark:text-red-400",
              qty === 0 && "text-green-600 dark:text-green-400",
            )}
          >
            {qty > 0 ? `+${qty}` : qty}
          </span>
        );
      },
    },
    {
      accessorKey: "variance_type",
      header: tCol("type"),
      cell: ({ row }) => {
        const type = row.original.variance_type as VarianceType;
        const colors = VARIANCE_TYPE_COLOR_MAP[type];
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent font-medium", colors.bg, colors.text)}
          >
            {tType(type)}
          </Badge>
        );
      },
    },
    {
      accessorKey: "resolution",
      header: tCol("resolution"),
      cell: ({ row }) => {
        const resolution = row.original.resolution as VarianceResolution | null;
        if (!resolution) return "\u2014";
        const colors = RESOLUTION_COLOR_MAP[resolution];
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent font-medium", colors.bg, colors.text)}
          >
            {tResolution(resolution)}
          </Badge>
        );
      },
    },
    {
      accessorKey: "resolved_by_username",
      header: tCol("resolvedBy"),
      cell: ({ row }) =>
        row.original.resolved_by_username ?? "\u2014",
      enableSorting: false,
    },
  ];
}
