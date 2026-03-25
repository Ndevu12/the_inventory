"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import type { AuditEntry } from "../types/audit.types"
import {
  AUDIT_ACTION_COLOR_MAP,
  isAuditAction,
} from "../helpers/audit-constants"

export interface AuditColumnLabels {
  timestamp: string
  action: string
  summary: string
  scope: string
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
  /** Localized action badge text (i18n), with server fallback inside implementation. */
  getActionLabel: (entry: AuditEntry) => string
  eventScopeLabel: (scope: "operational" | "platform") => string
  showScopeColumn?: boolean
}

export function getAuditColumns(
  actions: AuditColumnActions,
): ColumnDef<AuditEntry>[] {
  const {
    labels: L,
    getActionLabel,
    eventScopeLabel,
    showScopeColumn = true,
  } = actions
  const columns: ColumnDef<AuditEntry>[] = [
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
        const entry = row.original
        const action = entry.action
        const colors = isAuditAction(action)
          ? AUDIT_ACTION_COLOR_MAP[action]
          : undefined
        return (
          <Badge
            variant="outline"
            className={`${colors?.bg ?? ""} ${colors?.text ?? ""} border-transparent max-w-[min(100%,14rem)] whitespace-normal text-left`}
          >
            {getActionLabel(entry)}
          </Badge>
        )
      },
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true
        return filterValue.includes(row.original.action)
      },
    },
    {
      id: "summary",
      accessorFn: (row) => row.summary ?? "",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={L.summary} />
      ),
      cell: ({ row }) => {
        const summary = row.original.summary
        if (!summary)
          return <span className="text-muted-foreground">{L.emDash}</span>
        return (
          <span className="line-clamp-2 max-w-md text-sm" title={summary}>
            {summary}
          </span>
        )
      },
      enableSorting: false,
    },
    {
      id: "event_scope",
      accessorFn: (row) => row.event_scope ?? "",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={L.scope} />
      ),
      cell: ({ row }) => {
        const scope = row.original.event_scope
        if (!scope)
          return <span className="text-muted-foreground">{L.emDash}</span>
        const isPlatform = scope === "platform"
        return (
          <Badge
            variant="outline"
            className={
              isPlatform
                ? "border-transparent bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300"
                : "border-transparent bg-slate-100 text-slate-800 dark:bg-slate-800/40 dark:text-slate-300"
            }
          >
            {eventScopeLabel(scope)}
          </Badge>
        )
      },
      enableSorting: false,
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

  if (!showScopeColumn) {
    return columns.filter((column) => column.id !== "event_scope")
  }
  return columns
}
