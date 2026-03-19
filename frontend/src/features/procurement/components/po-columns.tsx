"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { DataTableColumnHeader, DataTableRowActions } from "@/components/data-table"
import type { RowAction } from "@/components/data-table/data-table-row-actions"
import type { PurchaseOrder } from "../types/procurement.types"
import { POStatusBadge } from "./purchase-orders/po-status-badge"

interface POColumnActions {
  onView: (po: PurchaseOrder) => void
  onConfirm?: (po: PurchaseOrder) => void
  onCancel?: (po: PurchaseOrder) => void
}

export function getPurchaseOrderColumns(
  actions: POColumnActions,
): ColumnDef<PurchaseOrder>[] {
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
      accessorKey: "supplier_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Supplier" />
      ),
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <POStatusBadge status={row.original.status} />
      ),
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true
        return filterValue.includes(row.original.status)
      },
    },
    {
      accessorKey: "order_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Order Date" />
      ),
      cell: ({ row }) =>
        new Date(row.original.order_date).toLocaleDateString(),
    },
    {
      accessorKey: "expected_delivery_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Expected Delivery" />
      ),
      cell: ({ row }) => {
        const date = row.original.expected_delivery_date
        return date ? new Date(date).toLocaleDateString() : "—"
      },
    },
    {
      accessorKey: "total_cost",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Total" />
      ),
      cell: ({ row }) => {
        const total = Number(row.original.total_cost)
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
        }).format(total)
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Created" />
      ),
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(),
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const po = row.original
        const rowActions: RowAction<PurchaseOrder>[] = [
          {
            label: "View",
            onClick: () => actions.onView(po),
          },
        ]

        if (po.status === "draft" && actions.onConfirm) {
          rowActions.push({
            label: "Confirm",
            onClick: () => actions.onConfirm!(po),
          })
        }

        if ((po.status === "draft" || po.status === "confirmed") && actions.onCancel) {
          rowActions.push({
            label: "Cancel",
            onClick: () => actions.onCancel!(po),
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
