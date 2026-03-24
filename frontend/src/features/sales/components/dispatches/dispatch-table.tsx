"use client"

import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import { useTranslations } from "next-intl"
import { DataTable } from "@/components/data-table/data-table"
import type { Dispatch } from "../../types/dispatch.types"

interface DispatchTableProps {
  columns: ColumnDef<Dispatch, unknown>[]
  data: Dispatch[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  isLoading?: boolean
  filterContent?: React.ReactNode
}

export function DispatchTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  isLoading,
  filterContent,
}: DispatchTableProps) {
  const t = useTranslations("Sales.dispatches.table")

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      isLoading={isLoading}
      emptyMessage={t("empty")}
      filterContent={filterContent}
    />
  )
}
