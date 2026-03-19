"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import type { AuditEntry } from "../types/audit.types"
import { AUDIT_ACTION_COLOR_MAP } from "../helpers/audit-constants"

interface AuditColumnActions {
  onViewDetails: (entry: AuditEntry) => void
}

export function getAuditColumns(
  actions: AuditColumnActions,
): ColumnDef<AuditEntry>[] {
  return [
    {
      accessorKey: "timestamp",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Timestamp" />
      ),
      cell: ({ row }) => {
        const ts = row.original.timestamp
        return new Date(ts).toLocaleString()
      },
    },
    {
      accessorKey: "action",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Action" />
      ),
      cell: ({ row }) => {
        const action = row.original.action
        const colors = AUDIT_ACTION_COLOR_MAP[action]
        return (
          <Badge
            variant="outline"
            className={`${colors?.bg ?? ""} ${colors?.text ?? ""} border-transparent`}
          >
            {row.original.action_display}
          </Badge>
        )
      },
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true
        return filterValue.includes(row.original.action)
      },
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Product" />
      ),
      cell: ({ row }) => {
        const { product_name, product_sku } = row.original
        if (!product_name) return <span className="text-muted-foreground">—</span>
        return (
          <div>
            <span className="font-medium">{product_name}</span>
            {product_sku && (
              <span className="ml-2 text-xs text-muted-foreground">
                {product_sku}
              </span>
            )}
          </div>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "username",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="User" />
      ),
      cell: ({ row }) =>
        row.original.username ?? (
          <span className="text-muted-foreground">System</span>
        ),
      enableSorting: false,
    },
    {
      accessorKey: "ip_address",
      header: "IP Address",
      cell: ({ row }) =>
        row.original.ip_address ?? (
          <span className="text-muted-foreground">—</span>
        ),
      enableSorting: false,
    },
    {
      id: "details",
      header: "",
      cell: ({ row }) => (
        <button
          type="button"
          onClick={() => actions.onViewDetails(row.original)}
          className="text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          View
        </button>
      ),
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
