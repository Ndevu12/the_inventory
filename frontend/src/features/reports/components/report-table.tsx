"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "@/components/data-table"

interface ReportTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  isLoading?: boolean
  emptyMessage?: string
}

export function ReportTable<TData, TValue>({
  columns,
  data,
  isLoading = false,
  emptyMessage = "No data for this report.",
}: ReportTableProps<TData, TValue>) {
  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage={emptyMessage}
    />
  )
}
