"use client"

import { DataTable } from "@/components/data-table"
import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import type { Supplier } from "../../types/procurement.types"

interface SupplierTableProps {
  columns: ColumnDef<Supplier, unknown>[]
  data: Supplier[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  isLoading?: boolean
  filterContent?: React.ReactNode
}

export function SupplierTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  isLoading,
  filterContent,
}: SupplierTableProps) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder="Search suppliers..."
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage="No suppliers found."
    />
  )
}
