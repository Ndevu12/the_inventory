"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import type { AuditEntry } from "../types/audit.types"
import { AUDIT_ACTION_COLOR_MAP } from "../helpers/audit-constants"

export interface AuditColumnLabels {
  timestamp: string
  action: string
  product: string
  user: string
  ipAddress: string
  view: string
  system: string
  emDash: string
}

interface AuditColumnActions {
  onViewDetails: (entry: AuditEntry) => void
  labels: AuditColumnLabels
}

export function getAuditColumns(
  actions: AuditColumnActions,
): ColumnDef<AuditEntry>[] {
  const { labels: L } = actions
  return [
    {
      accessorKey: "timestamp",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={L.timestamp} />
      ),
      cell: ({ row }) => {
        const ts = row.original.timestamp
        return new Date(ts).toLocaleString()
      },
    },
    {
      accessorKey: "action",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={L.action} />
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
        <DataTableColumnHeader column={column} title={L.product} />
      ),
      cell: ({ row }) => {
        const { product_name, product_sku } = row.original
        if (!product_name)
          return <span className="text-muted-foreground">{L.emDash}</span>
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
        <DataTableColumnHeader column={column} title={L.user} />
      ),
      cell: ({ row }) =>
        row.original.username ?? (
          <span className="text-muted-foreground">{L.system}</span>
        ),
      enableSorting: false,
    },
    {
      accessorKey: "ip_address",
      header: L.ipAddress,
      cell: ({ row }) =>
        row.original.ip_address ?? (
          <span className="text-muted-foreground">{L.emDash}</span>
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
          {L.view}
        </button>
      ),
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
