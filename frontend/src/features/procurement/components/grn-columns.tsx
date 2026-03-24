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

export interface GRNColumnLabels {
  tColumns: (key: string) => string
  emDash: string
  processedLabel: string
  pendingLabel: string
  viewLabel: string
  receiveGoodsLabel: string
  deleteLabel: string
  locale: string
}

export function getGRNColumns(
  actions: GRNColumnActions,
  labels: GRNColumnLabels,
): ColumnDef<GoodsReceivedNote>[] {
  const dateOpts: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  }

  return [
    {
      accessorKey: "grn_number",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("grnNumber")} />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("grn_number")}</span>
      ),
    },
    {
      accessorKey: "purchase_order_number",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("purchaseOrder")}
        />
      ),
      cell: ({ row }) => row.getValue("purchase_order_number") || labels.emDash,
      enableSorting: false,
    },
    {
      accessorKey: "received_date",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("receivedDate")}
        />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("received_date"))
        return (
          <span className="whitespace-nowrap text-sm">
            {date.toLocaleDateString(labels.locale, dateOpts)}
          </span>
        )
      },
    },
    {
      accessorKey: "location_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("location")} />
      ),
      cell: ({ row }) => row.getValue("location_name") || labels.emDash,
      enableSorting: false,
    },
    {
      accessorKey: "is_processed",
      header: labels.tColumns("status"),
      cell: ({ row }) => {
        const processed = row.getValue<boolean>("is_processed")
        return (
          <Badge variant={processed ? "default" : "secondary"}>
            {processed ? labels.processedLabel : labels.pendingLabel}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("created")} />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("created_at"))
        return (
          <span className="whitespace-nowrap text-sm text-muted-foreground">
            {date.toLocaleDateString(labels.locale, dateOpts)}
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
            label: labels.viewLabel,
            onClick: () => actions.onView!(grn),
          })
        }

        if (actions.onReceive && !grn.is_processed) {
          rowActions.push({
            label: labels.receiveGoodsLabel,
            onClick: () => actions.onReceive!(grn),
          })
        }

        if (actions.onDelete && !grn.is_processed) {
          rowActions.push({
            label: labels.deleteLabel,
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
