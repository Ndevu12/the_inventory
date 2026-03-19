"use client"

import type { ColumnDef, PaginationState, SortingState } from "@tanstack/react-table"
import { DataTable } from "@/components/data-table"
import type { Customer } from "../../types/sales.types"

interface CustomerTableProps {
  columns: ColumnDef<Customer, unknown>[]
  data: Customer[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  sorting: SortingState
  onSortingChange: (sorting: SortingState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  isLoading?: boolean
}

export function CustomerTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  sorting,
  onSortingChange,
  searchValue,
  onSearchChange,
  isLoading,
}: CustomerTableProps) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchPlaceholder="Search customers..."
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      isLoading={isLoading}
      emptyMessage="No customers found."
    />
  )
}
