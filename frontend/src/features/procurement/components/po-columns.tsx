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

export interface POColumnLabels {
  tColumns: (key: string) => string
  emDash: string
  viewLabel: string
  confirmLabel: string
  cancelLabel: string
  locale: string
}

export function getPurchaseOrderColumns(
  actions: POColumnActions,
  labels: POColumnLabels,
): ColumnDef<PurchaseOrder>[] {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat(labels.locale, {
      style: "currency",
      currency: "USD",
    }).format(value)

  return [
    {
      accessorKey: "order_number",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("orderNumber")}
        />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("order_number")}</span>
      ),
    },
    {
      accessorKey: "supplier_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("supplier")} />
      ),
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: labels.tColumns("status"),
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
        <DataTableColumnHeader column={column} title={labels.tColumns("orderDate")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.order_date).toLocaleDateString(labels.locale),
    },
    {
      accessorKey: "expected_delivery_date",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("expectedDelivery")}
        />
      ),
      cell: ({ row }) => {
        const date = row.original.expected_delivery_date
        return date
          ? new Date(date).toLocaleDateString(labels.locale)
          : labels.emDash
      },
    },
    {
      accessorKey: "total_cost",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("total")} />
      ),
      cell: ({ row }) => {
        const total = Number(row.original.total_cost)
        return formatCurrency(total)
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("created")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(labels.locale),
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const po = row.original
        const rowActions: RowAction<PurchaseOrder>[] = [
          {
            label: labels.viewLabel,
            onClick: () => actions.onView(po),
          },
        ]

        if (po.status === "draft" && actions.onConfirm) {
          rowActions.push({
            label: labels.confirmLabel,
            onClick: () => actions.onConfirm!(po),
          })
        }

        if ((po.status === "draft" || po.status === "confirmed") && actions.onCancel) {
          rowActions.push({
            label: labels.cancelLabel,
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
