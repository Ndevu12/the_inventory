"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { DataTableRowActions } from "@/components/data-table"
import type { Supplier } from "../types/procurement.types"
import { paymentTermsLabel } from "../helpers/procurement-constants"

interface SupplierColumnActions {
  onEdit: (supplier: Supplier) => void
  onDelete: (supplier: Supplier) => void
}

export function getSupplierColumns(
  actions: SupplierColumnActions
): ColumnDef<Supplier>[] {
  return [
    {
      accessorKey: "code",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Code" />
      ),
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("code")}</span>
      ),
    },
    {
      accessorKey: "name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Name" />
      ),
    },
    {
      accessorKey: "contact_name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Contact" />
      ),
      cell: ({ row }) => row.getValue("contact_name") || "—",
    },
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) => row.getValue("email") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "phone",
      header: "Phone",
      cell: ({ row }) => row.getValue("phone") || "—",
      enableSorting: false,
    },
    {
      accessorKey: "payment_terms",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Payment Terms" />
      ),
      cell: ({ row }) => {
        const s = row.original
        const fromApi = s.payment_terms_display?.trim()
        if (fromApi) return fromApi
        return paymentTermsLabel(s.payment_terms) || "—"
      },
    },
    {
      accessorKey: "lead_time_days",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Lead Time" />
      ),
      cell: ({ row }) => {
        const days = row.getValue<number>("lead_time_days")
        return `${days} day${days !== 1 ? "s" : ""}`
      },
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
      id: "actions",
      cell: ({ row }) => (
        <DataTableRowActions
          row={row}
          onEdit={(r) => actions.onEdit(r.original)}
          onDelete={(r) => actions.onDelete(r.original)}
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
  ]
}
