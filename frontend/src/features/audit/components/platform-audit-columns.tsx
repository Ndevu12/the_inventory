"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import type { PlatformAuditEntry } from "../types/audit.types"
import { AUDIT_ACTION_COLOR_MAP } from "../helpers/audit-constants"

interface PlatformAuditColumnActions {
  onViewDetails: (entry: PlatformAuditEntry) => void
}

const DEFAULT_COLORS = {
  bg: "bg-gray-100 dark:bg-gray-800/30",
  text: "text-gray-800 dark:text-gray-300",
}

function getActionColors(action: string) {
  return (
    (AUDIT_ACTION_COLOR_MAP as Record<string, { bg: string; text: string }>)[
      action
    ] ?? DEFAULT_COLORS
  )
}

export function getPlatformAuditColumns(
  actions: PlatformAuditColumnActions,
): ColumnDef<PlatformAuditEntry>[] {
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
      accessorKey: "tenant_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Tenant" />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.original.tenant_name}</span>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "action",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Action" />
      ),
      cell: ({ row }) => {
        const action = row.original.action
        const colors = getActionColors(action)
        return (
          <Badge
            variant="outline"
            className={`${colors.bg} ${colors.text} border-transparent`}
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
        if (!product_name)
          return <span className="text-muted-foreground">—</span>
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
