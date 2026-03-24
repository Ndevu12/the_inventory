"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { PencilIcon, TrashIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions } from "@/components/data-table"
import type { Supplier } from "../types/procurement.types"
import { paymentTermsLabel } from "../helpers/procurement-constants"

interface SupplierColumnActions {
  onEdit: (supplier: Supplier) => void
  onDelete: (supplier: Supplier) => void
}

export interface SupplierColumnLabels {
  tColumns: (key: string, values?: Record<string, number | string>) => string
  tPaymentTerms: (key: string) => string
  emDash: string
  activeLabel: string
  inactiveLabel: string
  editLabel: string
  deleteLabel: string
}

export function getSupplierColumns(
  actions: SupplierColumnActions,
  labels: SupplierColumnLabels,
): ColumnDef<Supplier>[] {
  return [
    {
      accessorKey: "code",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("code")} />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("code")}</span>
      ),
    },
    {
      accessorKey: "name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("name")} />
      ),
    },
    {
      accessorKey: "contact_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("contact")} />
      ),
      cell: ({ row }) => row.getValue("contact_name") || labels.emDash,
    },
    {
      accessorKey: "email",
      header: labels.tColumns("email"),
      cell: ({ row }) => row.getValue("email") || labels.emDash,
      enableSorting: false,
    },
    {
      accessorKey: "phone",
      header: labels.tColumns("phone"),
      cell: ({ row }) => row.getValue("phone") || labels.emDash,
      enableSorting: false,
    },
    {
      accessorKey: "payment_terms",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={labels.tColumns("paymentTerms")}
        />
      ),
      cell: ({ row }) => {
        const s = row.original
        const fromApi = s.payment_terms_display?.trim()
        if (fromApi) return fromApi
        return paymentTermsLabel(s.payment_terms, labels.tPaymentTerms) || labels.emDash
      },
    },
    {
      accessorKey: "lead_time_days",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={labels.tColumns("leadTime")} />
      ),
      cell: ({ row }) => {
        const days = row.getValue<number>("lead_time_days")
        return labels.tColumns("leadTimeDays", { count: days })
      },
    },
    {
      accessorKey: "is_active",
      header: labels.tColumns("status"),
      cell: ({ row }) => {
        const active = row.getValue<boolean>("is_active")
        return (
          <Badge variant={active ? "default" : "secondary"}>
            {active ? labels.activeLabel : labels.inactiveLabel}
          </Badge>
        )
      },
      enableSorting: false,
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <DataTableRowActions
          row={row}
          actions={[
            {
              label: labels.editLabel,
              icon: <PencilIcon className="mr-2 size-4" />,
              onClick: (r) => actions.onEdit(r.original),
            },
            {
              label: labels.deleteLabel,
              icon: <TrashIcon className="mr-2 size-4" />,
              onClick: (r) => actions.onDelete(r.original),
              variant: "destructive",
              separator: true,
            },
          ]}
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
