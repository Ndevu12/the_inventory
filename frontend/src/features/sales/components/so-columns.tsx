"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions, type RowAction } from "@/components/data-table"
import type { SalesOrder } from "../types/sales.types"
import { SOStatusBadge } from "./sales-orders/so-status-badge"
import { CanFulfillBadge } from "./sales-orders/can-fulfill-badge"

interface SOColumnActions {
  onView?: (so: SalesOrder) => void
  onConfirm?: (so: SalesOrder) => void
  onCancel?: (so: SalesOrder) => void
  onDelete?: (so: SalesOrder) => void
}

export function getSOColumns(
  actions: SOColumnActions,
): ColumnDef<SalesOrder>[] {
  return [
    {
      accessorKey: "order_number",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Order #" />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("order_number")}</span>
      ),
    },
    {
      accessorKey: "customer_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Customer" />
      ),
      cell: ({ row }) => row.getValue("customer_name") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "order_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Order Date" />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("order_date"))
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
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <SOStatusBadge status={row.original.status} />
      ),
      enableSorting: false,
    },
    {
      accessorKey: "total_price",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Total" />
      ),
      cell: ({ row }) => {
        const val = row.getValue<string>("total_price")
        return (
          <span className="whitespace-nowrap font-medium tabular-nums">
            {parseFloat(val).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "can_fulfill",
      header: "Fulfillment",
      cell: ({ row }) => <CanFulfillBadge canFulfill={row.original.can_fulfill} />,
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
        const so = row.original
        const rowActions: RowAction<SalesOrder>[] = []

        if (actions.onView) {
          rowActions.push({
            label: "View",
            onClick: () => actions.onView!(so),
          })
        }

        if (actions.onConfirm && so.status === "draft") {
          rowActions.push({
            label: "Confirm",
            onClick: () => actions.onConfirm!(so),
          })
        }

        if (actions.onCancel && (so.status === "draft" || so.status === "confirmed")) {
          rowActions.push({
            label: "Cancel",
            onClick: () => actions.onCancel!(so),
          })
        }

        if (actions.onDelete && so.status === "draft") {
          rowActions.push({
            label: "Delete",
            onClick: () => actions.onDelete!(so),
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
