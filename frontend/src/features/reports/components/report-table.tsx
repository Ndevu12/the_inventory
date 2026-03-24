"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { useTranslations } from "next-intl"
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
  emptyMessage,
}: ReportTableProps<TData, TValue>) {
  const t = useTranslations("Reports.shared")
  const resolvedEmpty = emptyMessage ?? t("emptyDefault")
  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage={resolvedEmpty}
    />
  )
}
