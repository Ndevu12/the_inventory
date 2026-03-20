"use client"

import type {
  ColumnDef,
  PaginationState,
  SortingState,
} from "@tanstack/react-table"
import { DataTable } from "@/components/data-table"
import type { PurchaseOrder } from "../../types/procurement.types"

interface POTableProps {
  columns: ColumnDef<PurchaseOrder, unknown>[]
  data: PurchaseOrder[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (state: PaginationState) => void
  sorting: SortingState
  onSortingChange: (state: SortingState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  filterContent?: React.ReactNode
  isLoading?: boolean
}

export function POTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  sorting,
  onSortingChange,
  searchValue,
  onSearchChange,
  filterContent,
  isLoading,
}: POTableProps) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      sorting={sorting}
      onSortingChange={onSortingChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder="Search purchase orders..."
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage="No purchase orders found."
    />
  )
}
