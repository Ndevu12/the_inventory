"use client"

import type { Row } from "@tanstack/react-table"
import { EllipsisIcon, EyeIcon, PencilIcon, TrashIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export interface RowAction<TData> {
  label: string
  icon?: React.ReactNode
  onClick: (row: Row<TData>) => void
  variant?: "default" | "destructive"
  separator?: boolean
}

interface DataTableRowActionsProps<TData> {
  row: Row<TData>
  actions?: RowAction<TData>[]
  onView?: (row: Row<TData>) => void
  onEdit?: (row: Row<TData>) => void
  onDelete?: (row: Row<TData>) => void
}

export function DataTableRowActions<TData>({
  row,
  actions,
  onView,
  onEdit,
  onDelete,
}: DataTableRowActionsProps<TData>) {
  const defaultActions: RowAction<TData>[] = []

  if (onView) {
    defaultActions.push({
      label: "View",
      icon: <EyeIcon />,
      onClick: onView,
    })
  }

  if (onEdit) {
    defaultActions.push({
      label: "Edit",
      icon: <PencilIcon />,
      onClick: onEdit,
    })
  }

  if (onDelete) {
    defaultActions.push({
      label: "Delete",
      icon: <TrashIcon />,
      onClick: onDelete,
      variant: "destructive",
      separator: true,
    })
  }

  const allActions = actions ?? defaultActions

  if (allActions.length === 0) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="flex size-8 data-[state=open]:bg-muted"
          />
        }
      >
        <EllipsisIcon className="size-4" />
        <span className="sr-only">Open menu</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {allActions.map((action, index) => (
          <div key={action.label}>
            {action.separator && index > 0 && <DropdownMenuSeparator />}
            <DropdownMenuItem
              variant={action.variant}
              onClick={() => action.onClick(row)}
            >
              {action.icon}
              {action.label}
            </DropdownMenuItem>
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
