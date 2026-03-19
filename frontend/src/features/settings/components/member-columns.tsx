"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { cn } from "@/lib/utils"
import { ROLE_MAP, ROLE_COLOR_MAP } from "../helpers/settings-constants"
import { MemberRoleSelect } from "./member-role-select"
import type { TenantMember, TenantRole } from "../types/settings.types"

interface MemberColumnActions {
  onRoleChange: (member: TenantMember, role: TenantRole) => void
  onRemove: (member: TenantMember) => void
  isUpdating?: boolean
}

function fullName(member: TenantMember): string {
  const name = [member.first_name, member.last_name].filter(Boolean).join(" ")
  return name || member.username
}

export function getMemberColumns(
  actions: MemberColumnActions
): ColumnDef<TenantMember>[] {
  return [
    {
      accessorKey: "username",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="User" />
      ),
      cell: ({ row }) => {
        const member = row.original
        return (
          <div className="flex flex-col">
            <span className="font-medium">{fullName(member)}</span>
            <span className="text-xs text-muted-foreground">
              @{member.username}
            </span>
          </div>
        )
      },
    },
    {
      accessorKey: "email",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Email" />
      ),
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.getValue("email") || "—"}
        </span>
      ),
    },
    {
      accessorKey: "role",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Role" />
      ),
      cell: ({ row }) => {
        const member = row.original
        const isOwner = member.role === "owner"

        if (isOwner) {
          const colors = ROLE_COLOR_MAP[member.role]
          return (
            <Badge
              variant="outline"
              className={cn(
                "border-transparent font-medium",
                colors.bg,
                colors.text
              )}
            >
              {ROLE_MAP[member.role]}
            </Badge>
          )
        }

        return (
          <MemberRoleSelect
            value={member.role}
            onValueChange={(role) => actions.onRoleChange(member, role)}
            disabled={actions.isUpdating}
          />
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => {
        const active = row.getValue<boolean>("is_active")
        return (
          <Badge variant={active ? "default" : "secondary"}>
            {active ? "Active" : "Inactive"}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Joined" />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue<string>("created_at"))
        return date.toLocaleDateString()
      },
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const member = row.original
        if (member.role === "owner") return null

        return (
          <RemoveButton onClick={() => actions.onRemove(member)} />
        )
      },
      enableSorting: false,
      enableHiding: false,
    },
  ]
}

import { TrashIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="size-8 text-muted-foreground hover:text-destructive"
      onClick={onClick}
    >
      <TrashIcon className="size-4" />
      <span className="sr-only">Remove member</span>
    </Button>
  )
}
