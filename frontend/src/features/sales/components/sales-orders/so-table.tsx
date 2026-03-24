"use client"

import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import { useTranslations } from "next-intl"
import { DataTable } from "@/components/data-table/data-table"
import type { SalesOrder } from "../../types/sales.types"

interface SOTableProps {
  columns: ColumnDef<SalesOrder, unknown>[]
  data: SalesOrder[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  isLoading?: boolean
  filterContent?: React.ReactNode
}

export function SOTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  isLoading,
  filterContent,
}: SOTableProps) {
  const t = useTranslations("Sales.salesOrders.table")

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchPlaceholder={t("searchPlaceholder")}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      isLoading={isLoading}
      emptyMessage={t("empty")}
      filterContent={filterContent}
    />
  )
}
