"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions, type RowAction } from "@/components/data-table"
import type { GoodsReceivedNote } from "../types/grn.types"

interface GRNColumnActions {
  onView?: (grn: GoodsReceivedNote) => void
  onReceive?: (grn: GoodsReceivedNote) => void
  onDelete?: (grn: GoodsReceivedNote) => void
}

export function getGRNColumns(
  actions: GRNColumnActions,
): ColumnDef<GoodsReceivedNote>[] {
  return [
    {
      accessorKey: "grn_number",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="GRN #" />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("grn_number")}</span>
      ),
    },
    {
      accessorKey: "purchase_order_number",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Purchase Order" />
      ),
      cell: ({ row }) => row.getValue("purchase_order_number") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "received_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Received Date" />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("received_date"))
        return (
          <span className="whitespace-nowrap text-sm">
            {date.toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        )
      },
    },
    {
      accessorKey: "location_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Location" />
      ),
      cell: ({ row }) => row.getValue("location_name") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "is_processed",
      header: "Status",
      cell: ({ row }) => {
        const processed = row.getValue<boolean>("is_processed")
        return (
          <Badge variant={processed ? "default" : "secondary"}>
            {processed ? "Processed" : "Pending"}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Created" />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("created_at"))
        return (
          <span className="whitespace-nowrap text-sm text-muted-foreground">
            {date.toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        )
      },
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const grn = row.original
        const rowActions: RowAction<GoodsReceivedNote>[] = []

        if (actions.onView) {
          rowActions.push({
            label: "View",
            onClick: () => actions.onView!(grn),
          })
        }

        if (actions.onReceive && !grn.is_processed) {
          rowActions.push({
            label: "Receive Goods",
            onClick: () => actions.onReceive!(grn),
          })
        }

        if (actions.onDelete && !grn.is_processed) {
          rowActions.push({
            label: "Delete",
            onClick: () => actions.onDelete!(grn),
            variant: "destructive",
            separator: true,
          })
        }

        return <DataTableRowActions row={row} actions={rowActions} />
      },
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
