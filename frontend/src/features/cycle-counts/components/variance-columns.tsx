"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { InventoryVariance } from "../types/cycle-count.types";
import {
  VARIANCE_TYPE_COLOR_MAP,
  RESOLUTION_COLOR_MAP,
} from "../helpers/cycle-constants";

export function getVarianceColumns(): ColumnDef<InventoryVariance, unknown>[] {
  return [
    {
      accessorKey: "product_name",
      header: "Product",
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
      header: "Location",
      enableSorting: false,
    },
    {
      accessorKey: "system_quantity",
      header: "System Qty",
    },
    {
      accessorKey: "physical_quantity",
      header: "Physical Qty",
    },
    {
      accessorKey: "variance_quantity",
      header: "Variance",
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
      header: "Type",
      cell: ({ row }) => {
        const type = row.original.variance_type;
        const colors = VARIANCE_TYPE_COLOR_MAP[type];
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent font-medium", colors.bg, colors.text)}
          >
            {row.original.variance_type_display}
          </Badge>
        );
      },
    },
    {
      accessorKey: "resolution",
      header: "Resolution",
      cell: ({ row }) => {
        const resolution = row.original.resolution;
        if (!resolution) return "—";
        const colors = RESOLUTION_COLOR_MAP[resolution];
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent font-medium", colors.bg, colors.text)}
          >
            {row.original.resolution_display}
          </Badge>
        );
      },
    },
    {
      accessorKey: "resolved_by_username",
      header: "Resolved By",
      cell: ({ row }) => row.original.resolved_by_username ?? "—",
      enableSorting: false,
    },
  ];
}
