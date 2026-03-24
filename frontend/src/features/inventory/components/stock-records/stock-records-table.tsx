"use client"

import { useMemo } from "react"
import { useTranslations } from "next-intl"
import { DataTable } from "@/components/data-table/data-table"
import { createStockRecordColumns } from "../../helpers/stock-record-columns"
import type { StockRecord } from "../../types/inventory.types"

interface StockRecordsTableProps {
  data: StockRecord[]
  pageCount?: number
  searchValue?: string
  onSearchChange?: (value: string) => void
  filterContent?: React.ReactNode
}

export function StockRecordsTable({
  data,
  pageCount,
  searchValue,
  onSearchChange,
  filterContent,
}: StockRecordsTableProps) {
  const t = useTranslations("Inventory")

  const columns = useMemo(
    () => createStockRecordColumns((key) => t(key as never)),
    [t],
  )

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      searchKey="product_name"
      searchPlaceholder={t("stockRecords.searchPlaceholder")}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      filterContent={filterContent}
      noResultsMessage={t("stockRecords.empty")}
    />
  )
}
