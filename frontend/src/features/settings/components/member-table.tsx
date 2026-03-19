"use client"

import { DataTable } from "@/components/data-table"
import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import type { TenantMember } from "../types/settings.types"

interface MemberTableProps {
  columns: ColumnDef<TenantMember, unknown>[]
  data: TenantMember[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  searchValue: string
  onSearchChange: (value: string) => void
  isLoading?: boolean
  filterContent?: React.ReactNode
}

export function MemberTable({
  columns,
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  isLoading,
  filterContent,
}: MemberTableProps) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder="Search members..."
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage="No team members found."
    />
  )
}
