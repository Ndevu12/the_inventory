"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions, type RowAction } from "@/components/data-table"
import type { Dispatch } from "../types/dispatch.types"

interface DispatchColumnActions {
  onView?: (dispatch: Dispatch) => void
  onProcess?: (dispatch: Dispatch) => void
  onDelete?: (dispatch: Dispatch) => void
}

export function getDispatchColumns(
  actions: DispatchColumnActions,
): ColumnDef<Dispatch>[] {
  return [
    {
      accessorKey: "dispatch_number",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Dispatch #" />
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
        <DataTableColumnHeader column={column} title="Sales Order" />
      ),
      cell: ({ row }) => row.getValue("sales_order_number") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "dispatch_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Dispatch Date" />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("dispatch_date"))
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
      accessorKey: "from_location_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="From Location" />
      ),
      cell: ({ row }) => row.getValue("from_location_name") || "—",
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
        const dispatch = row.original
        const rowActions: RowAction<Dispatch>[] = []

        if (actions.onView) {
          rowActions.push({
            label: "View",
            onClick: () => actions.onView!(dispatch),
          })
        }

        if (actions.onProcess && !dispatch.is_processed) {
          rowActions.push({
            label: "Process Dispatch",
            onClick: () => actions.onProcess!(dispatch),
          })
        }

        if (actions.onDelete && !dispatch.is_processed) {
          rowActions.push({
            label: "Delete",
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
