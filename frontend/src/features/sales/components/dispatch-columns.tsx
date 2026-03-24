"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions, type RowAction } from "@/components/data-table"
import type { Dispatch } from "../types/dispatch.types"

interface DispatchColumnActions {
  onView?: (dispatch: Dispatch) => void
  onProcess?: (dispatch: Dispatch) => void
  /** Open stock preview: available qty at source vs ordered; partial issue. */
  onReviewStock?: (dispatch: Dispatch) => void
  onDelete?: (dispatch: Dispatch) => void
}

export interface DispatchColumnLabels {
  tColumns: (key: string) => string
  emDash: string
  processedLabel: string
  pendingLabel: string
  viewLabel: string
  reviewStockLabel: string
  processDispatchLabel: string
  deleteLabel: string
  locale: string
}

export function getDispatchColumns(
  actions: DispatchColumnActions,
  labels: DispatchColumnLabels,
): ColumnDef<Dispatch>[] {
  return [
    {
      accessorKey: "dispatch_number",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("dispatchNumber")}
        />
      ),
      cell: ({ row }) => (
        <span className="font-medium">
          {row.getValue("dispatch_number")}
        </span>
      ),
    },
    {
      accessorKey: "sales_order_number",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("salesOrder")}
        />
      ),
      cell: ({ row }) => row.getValue("sales_order_number") || labels.emDash,
      enableSorting: false,
    },
    {
      accessorKey: "dispatch_date",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("dispatchDate")}
        />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("dispatch_date"))
        return (
          <span className="whitespace-nowrap text-sm">
            {date.toLocaleDateString(labels.locale, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        )
      },
    },
    {
      accessorKey: "from_location_name",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("fromLocation")}
        />
      ),
      cell: ({ row }) => row.getValue("from_location_name") || labels.emDash,
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
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("created")}
        />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("created_at"))
        return (
          <span className="whitespace-nowrap text-sm text-muted-foreground">
            {date.toLocaleDateString(labels.locale, {
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
        const dispatch = row.original
        const rowActions: RowAction<Dispatch>[] = []

        if (actions.onView) {
          rowActions.push({
            label: labels.viewLabel,
            onClick: () => actions.onView!(dispatch),
          })
        }

        if (actions.onReviewStock && !dispatch.is_processed) {
          rowActions.push({
            label: labels.reviewStockLabel,
            onClick: () => actions.onReviewStock!(dispatch),
          })
        }

        if (actions.onProcess && !dispatch.is_processed) {
          rowActions.push({
            label: labels.processDispatchLabel,
            onClick: () => actions.onProcess!(dispatch),
          })
        }

        if (actions.onDelete && !dispatch.is_processed) {
          rowActions.push({
            label: labels.deleteLabel,
            onClick: () => actions.onDelete!(dispatch),
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
