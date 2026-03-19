"use client"

import { DataTable } from "@/components/data-table"
import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import type { GoodsReceivedNote } from "../../types/grn.types"

interface GRNTableProps {
  columns: ColumnDef<GoodsReceivedNote, unknown>[]
  data: GoodsReceivedNote[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  isLoading?: boolean
  filterContent?: React.ReactNode
}

export function GRNTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  isLoading,
  filterContent,
}: GRNTableProps) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage="No GRNs found."
    />
  )
}
