"use client"

import type { ColumnDef, Row } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader, DataTableRowActions } from "@/components/data-table"
import type { PlatformInvitation } from "../types/settings.types"
import { ROLE_COLOR_MAP } from "../helpers/settings-constants"
import { cn } from "@/lib/utils"
import type { TenantRole } from "../types/settings.types"

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-800 dark:text-amber-200" },
  accepted: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-200" },
  cancelled: { bg: "bg-gray-100 dark:bg-gray-800/30", text: "text-gray-800 dark:text-gray-300" },
  expired: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-200" },
}

interface PlatformInvitationColumnActions {
  onCancel: (invitation: PlatformInvitation) => void
  onResend: (invitation: PlatformInvitation) => void
  isCancelling?: boolean
  isResending?: boolean
  t: (key: string) => string
  roleLabel: (role: TenantRole) => string
}

export function getPlatformInvitationColumns(
  actions: PlatformInvitationColumnActions,
): ColumnDef<PlatformInvitation>[] {
  const { t, roleLabel } = actions
  return [
    {
      accessorKey: "email",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.email")} />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.original.email}</span>
      ),
    },
    {
      accessorKey: "tenant_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.tenant")} />
      ),
      cell: ({ row }) => row.original.tenant_name,
      enableSorting: false,
    },
    {
      accessorKey: "role",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.role")} />
      ),
      cell: ({ row }) => {
        const role = row.original.role as TenantRole
        const colors = ROLE_COLOR_MAP[role] ?? { bg: "", text: "" }
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent font-medium", colors.bg, colors.text)}
          >
            {roleLabel(role)}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.status")} />
      ),
      cell: ({ row }) => {
        const status = row.original.status
        const colors = STATUS_COLORS[status] ?? STATUS_COLORS.cancelled
        const label = t(`status.${status}`)
        return (
          <Badge
            variant="outline"
            className={cn("border-transparent capitalize", colors.bg, colors.text)}
          >
            {label}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.created")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
    },
    {
      accessorKey: "expires_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("columns.expires")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.expires_at).toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
    },
    {
      accessorKey: "invited_by_username",
      header: t("columns.invitedBy"),
      cell: ({ row }) =>
        row.original.invited_by_username ?? (
          <span className="text-muted-foreground">—</span>
        ),
      enableSorting: false,
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const inv = row.original
        if (inv.status !== "pending") return null

        return (
          <DataTableRowActions
            row={row as Row<PlatformInvitation>}
            actions={[
              {
                label: t("rowCancel"),
                icon: null,
                onClick: () => actions.onCancel(inv),
                variant: "destructive",
              },
              {
                label: t("rowResend"),
                icon: null,
                onClick: () => actions.onResend(inv),
              },
            ]}
          />
        )
      },
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
