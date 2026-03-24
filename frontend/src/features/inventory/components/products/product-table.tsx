"use client"

import { useMemo } from "react"
import { useRouter } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import { EyeIcon, PencilIcon, TrashIcon } from "lucide-react"
import type { PaginationState, Row } from "@tanstack/react-table"
import { DataTable } from "@/components/data-table/data-table"
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header"
import { DataTableRowActions } from "@/components/data-table/data-table-row-actions"
import { Badge } from "@/components/ui/badge"
import type { Product } from "../../types/inventory.types"
import { createProductColumns } from "../../helpers/product-columns"
import { formatCurrency, formatDate } from "../../helpers/inventory-formatters"

interface ProductTableProps {
  data: Product[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  filterContent?: React.ReactNode
  isLoading?: boolean
  onDelete?: (id: number) => void
}

export function ProductTable({
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  filterContent,
  isLoading,
  onDelete,
}: ProductTableProps) {
  const router = useRouter()
  const t = useTranslations("Inventory")

  const columns = useMemo(() => {
    const base = createProductColumns((key) => t(key as never))

    return [
      {
        ...base[0],
        header: ({ column }: { column: Parameters<typeof DataTableColumnHeader>[0]["column"] }) => (
          <DataTableColumnHeader column={column} title={t("products.columns.sku")} />
        ),
        cell: ({ row }: { row: { original: Product } }) => (
          <span className="font-mono text-xs">{row.original.sku}</span>
        ),
      },
      {
        ...base[1],
        header: ({ column }: { column: Parameters<typeof DataTableColumnHeader>[0]["column"] }) => (
          <DataTableColumnHeader column={column} title={t("products.columns.name")} />
        ),
        cell: ({ row }: { row: { original: Product } }) => (
          <span className="font-medium">{row.original.name}</span>
        ),
      },
      base[2],
      base[3],
      {
        ...base[4],
        header: ({ column }: { column: Parameters<typeof DataTableColumnHeader>[0]["column"] }) => (
          <DataTableColumnHeader column={column} title={t("products.columns.unitCost")} />
        ),
        cell: ({ row }: { row: { original: Product } }) => (
          <span className="tabular-nums">
            {formatCurrency(row.original.unit_cost)}
          </span>
        ),
      },
      base[5],
      {
        ...base[6],
        cell: ({ row }: { row: { original: Product } }) => (
          <Badge variant={row.original.is_active ? "default" : "secondary"}>
            {row.original.is_active ? t("shared.active") : t("shared.inactive")}
          </Badge>
        ),
      },
      {
        ...base[7],
        header: ({ column }: { column: Parameters<typeof DataTableColumnHeader>[0]["column"] }) => (
          <DataTableColumnHeader column={column} title={t("products.columns.created")} />
        ),
        cell: ({ row }: { row: { original: Product } }) =>
          formatDate(row.original.created_at),
      },
      {
        id: "actions",
        cell: ({ row }: { row: { original: Product } }) => (
          <DataTableRowActions
            row={row as never}
            actions={[
              {
                label: t("tableActions.view"),
                icon: <EyeIcon />,
                onClick: (r: Row<Product>) => {
                  router.push(`/products/${r.original.id}`)
                },
              },
              {
                label: t("tableActions.edit"),
                icon: <PencilIcon />,
                onClick: (r: Row<Product>) => {
                  router.push(`/products/${r.original.id}/edit`)
                },
              },
              ...(onDelete
                ? [
                    {
                      label: t("tableActions.delete"),
                      icon: <TrashIcon />,
                      onClick: (r: Row<Product>) => {
                        onDelete(r.original.id)
                      },
                      variant: "destructive" as const,
                      separator: true as const,
                    },
                  ]
                : []),
            ]}
          />
        ),
      },
    ]
  }, [router, onDelete, t])

  return (
    <DataTable
      columns={columns as never}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder={t("products.searchPlaceholder")}
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage={t("products.empty")}
    />
  )
}
