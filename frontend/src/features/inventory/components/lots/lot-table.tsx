"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import type { ColumnDef, PaginationState, SortingState } from "@tanstack/react-table"
import {
  DataTable,
  DataTableColumnHeader,
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table"
import { Badge } from "@/components/ui/badge"
import { ExpiryBadge } from "./expiry-badge"
import { createLotColumns } from "../../helpers/lot-columns"
import type { StockLot } from "../../types/lot.types"

interface LotTableProps {
  data: StockLot[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: React.Dispatch<React.SetStateAction<PaginationState>>
  sorting: SortingState
  onSortingChange: React.Dispatch<React.SetStateAction<SortingState>>
  searchValue: string
  onSearchChange: (value: string) => void
  activeFilter: string | undefined
  onActiveFilterChange: (value: string | undefined) => void
}

export function LotTable({
  data,
  pageCount,
  pagination,
  onPaginationChange,
  sorting,
  onSortingChange,
  searchValue,
  onSearchChange,
  activeFilter,
  onActiveFilterChange,
}: LotTableProps) {
  const t = useTranslations("Inventory")

  const activeOptions = React.useMemo<FacetedFilterOption[]>(
    () => [
      { label: t("shared.active"), value: "true" },
      { label: t("shared.inactive"), value: "false" },
    ],
    [t],
  )

  const columns = React.useMemo<ColumnDef<StockLot, unknown>[]>(() => {
    const base = createLotColumns((key) => t(key as never))
    return base.map((col) => {
      if ("accessorKey" in col || "id" in col) {
        const key = "accessorKey" in col ? String(col.accessorKey) : col.id

        if (
          key &&
          [
            "lot_number",
            "product_sku",
            "serial_number",
            "quantity_received",
            "quantity_remaining",
            "received_date",
            "expiry_date",
          ].includes(key)
        ) {
          return {
            ...col,
            header: ({ column }) => (
              <DataTableColumnHeader
                column={column}
                title={String(col.header)}
              />
            ),
          } as ColumnDef<StockLot, unknown>
        }

        if (key === "expiry_status") {
          return {
            ...col,
            header: ({ column }) => (
              <DataTableColumnHeader
                column={column}
                title={String(col.header)}
              />
            ),
            cell: ({ row }) => (
              <ExpiryBadge
                daysToExpiry={row.original.days_to_expiry}
                isExpired={row.original.is_expired}
              />
            ),
          } as ColumnDef<StockLot, unknown>
        }

        if (key === "is_active") {
          return {
            ...col,
            header: ({ column }) => (
              <DataTableColumnHeader
                column={column}
                title={String(col.header)}
              />
            ),
            cell: ({ row }) => (
              <Badge variant={row.original.is_active ? "default" : "secondary"}>
                {row.original.is_active ? t("shared.active") : t("shared.inactive")}
              </Badge>
            ),
          } as ColumnDef<StockLot, unknown>
        }
      }
      return col as ColumnDef<StockLot, unknown>
    })
  }, [t])

  const filterContent = React.useMemo(() => {
    return (
      <ActiveFilterProxy
        value={activeFilter}
        onChange={onActiveFilterChange}
        options={activeOptions}
        title={t("filters.status")}
      />
    )
  }, [activeFilter, onActiveFilterChange, activeOptions, t])

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
      searchPlaceholder={t("lots.searchPlaceholder")}
      filterContent={filterContent}
      noResultsMessage={t("lots.empty")}
    />
  )
}

function ActiveFilterProxy({
  value,
  onChange,
  options,
  title,
}: {
  value: string | undefined
  onChange: (v: string | undefined) => void
  options: FacetedFilterOption[]
  title: string
}) {
  const pseudoColumn = React.useMemo(
    () => ({
      getFacetedUniqueValues: () => new Map<string, number>(),
      getFilterValue: () => (value ? [value] : undefined),
      setFilterValue: (val: string[] | undefined) => {
        onChange(val?.[0])
      },
    }),
    [value, onChange],
  )

  return (
    <DataTableFacetedFilter
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      column={pseudoColumn as any}
      title={title}
      options={options}
    />
  )
}
