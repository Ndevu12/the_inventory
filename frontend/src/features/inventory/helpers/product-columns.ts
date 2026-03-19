import type { ColumnDef } from "@tanstack/react-table"
import type { Product } from "../types/inventory.types"
import { formatCurrency, formatDate } from "./inventory-formatters"

export function getProductColumns(): ColumnDef<Product>[] {
  return [
    {
      accessorKey: "sku",
      header: "SKU",
      enableSorting: true,
    },
    {
      accessorKey: "name",
      header: "Name",
      enableSorting: true,
    },
    {
      accessorKey: "category_name",
      header: "Category",
      cell: ({ row }) => row.original.category_name ?? "—",
    },
    {
      accessorKey: "unit_of_measure_display",
      header: "Unit",
    },
    {
      accessorKey: "unit_cost",
      header: "Unit Cost",
      cell: ({ row }) => formatCurrency(row.original.unit_cost),
      enableSorting: true,
    },
    {
      accessorKey: "reorder_point",
      header: "Reorder Pt.",
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (row.original.is_active ? "Active" : "Inactive"),
      filterFn: (row, _id, value: string[]) => {
        if (!value?.length) return true
        return value.includes(String(row.original.is_active))
      },
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => formatDate(row.original.created_at),
      enableSorting: true,
    },
  ]
}
