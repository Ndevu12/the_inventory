import type { ColumnDef } from "@tanstack/react-table"
import type { Product } from "../types/inventory.types"
import { formatCurrency, formatDate } from "./inventory-formatters"

type ProductColumnT = (key: string) => string

export function createProductColumns(t: ProductColumnT): ColumnDef<Product>[] {
  return [
    {
      accessorKey: "sku",
      header: t("products.columns.sku"),
      enableSorting: true,
    },
    {
      accessorKey: "name",
      header: t("products.columns.name"),
      enableSorting: true,
    },
    {
      accessorKey: "category_name",
      header: t("products.columns.category"),
      cell: ({ row }) =>
        row.original.category_name ?? t("shared.emDash"),
    },
    {
      accessorKey: "unit_of_measure_display",
      header: t("products.columns.unit"),
    },
    {
      accessorKey: "unit_cost",
      header: t("products.columns.unitCost"),
      cell: ({ row }) => formatCurrency(row.original.unit_cost),
      enableSorting: true,
    },
    {
      accessorKey: "reorder_point",
      header: t("products.columns.reorderPt"),
    },
    {
      accessorKey: "is_active",
      header: t("products.columns.status"),
      cell: ({ row }) =>
        row.original.is_active
          ? t("shared.active")
          : t("shared.inactive"),
      filterFn: (row, _id, value: string[]) => {
        if (!value?.length) return true
        return value.includes(String(row.original.is_active))
      },
    },
    {
      accessorKey: "created_at",
      header: t("products.columns.created"),
      cell: ({ row }) => formatDate(row.original.created_at),
      enableSorting: true,
    },
  ]
}
