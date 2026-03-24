"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { EyeIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { DataTableRowActions } from "@/components/data-table/data-table-row-actions";
import type { StockMovement, MovementType } from "../api/movements-api";

const TYPE_VARIANT: Record<
  MovementType,
  "default" | "secondary" | "outline" | "destructive"
> = {
  receive: "default",
  issue: "destructive",
  transfer: "secondary",
  adjustment: "outline",
};

type MovementT = (key: string) => string;

export function getMovementColumns(
  t: MovementT,
  onView?: (movement: StockMovement) => void,
): ColumnDef<StockMovement>[] {
  return [
    {
      accessorKey: "id",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.id")} />
      ),
      cell: ({ row }) => (
        <span className="font-mono text-xs">#{row.original.id}</span>
      ),
      size: 80,
    },
    {
      accessorKey: "movement_type",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.type")} />
      ),
      cell: ({ row }) => {
        const type = row.original.movement_type;
        return (
          <Badge variant={TYPE_VARIANT[type]}>
            {row.original.movement_type_display}
          </Badge>
        );
      },
      filterFn: (row, _id, value: string[]) =>
        value.includes(row.original.movement_type),
      size: 120,
    },
    {
      accessorKey: "product_sku",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("movements.columns.product")}
        />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.original.product_sku}</span>
      ),
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.qty")} />
      ),
      cell: ({ row }) => (
        <span className="font-mono tabular-nums">{row.original.quantity}</span>
      ),
      size: 80,
    },
    {
      accessorKey: "from_location_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.from")} />
      ),
      cell: ({ row }) =>
        row.original.from_location_name ?? t("shared.emDash"),
    },
    {
      accessorKey: "to_location_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.to")} />
      ),
      cell: ({ row }) =>
        row.original.to_location_name ?? t("shared.emDash"),
    },
    {
      accessorKey: "reference",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("movements.columns.reference")}
        />
      ),
      cell: ({ row }) => row.original.reference || t("shared.emDash"),
      size: 140,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("movements.columns.date")} />
      ),
      cell: ({ row }) => {
        const date = new Date(row.original.created_at);
        return (
          <span className="whitespace-nowrap text-sm text-muted-foreground">
            {date.toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}{" "}
            {date.toLocaleTimeString(undefined, {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        );
      },
    },
    {
      id: "actions",
      cell: ({ row }) =>
        onView ? (
          <DataTableRowActions
            row={row}
            actions={[
              {
                label: t("tableActions.view"),
                icon: <EyeIcon />,
                onClick: (r) => {
                  onView(r.original);
                },
              },
            ]}
          />
        ) : null,
      size: 50,
    },
  ];
}
