"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { useTranslations } from "next-intl"

import { DataTable } from "@/components/data-table/data-table"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { Input } from "@/components/ui/input"
import { getAuditActionFilterOptions } from "../helpers/audit-constants"
import type { AuditEntry } from "../types/audit.types"
import { getAuditColumns, type AuditColumnLabels } from "./audit-columns"

interface AuditTableProps {
  data: AuditEntry[]
  pageCount: number
  pagination: PaginationState
  onPaginationChange: (state: PaginationState) => void
  isLoading?: boolean
  actionFilter: string[]
  onActionFilterChange: (values: string[]) => void
  dateFrom: string
  onDateFromChange: (value: string) => void
  dateTo: string
  onDateToChange: (value: string) => void
  onViewDetails: (entry: AuditEntry) => void
}

export function AuditTable({
  data,
  pageCount,
  pagination,
  onPaginationChange,
  isLoading = false,
  actionFilter,
  onActionFilterChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  onViewDetails,
}: AuditTableProps) {
  const tPage = useTranslations("Audit.tenantPage")
  const tCols = useTranslations("Audit.columns")
  const tAudit = useTranslations("Audit")
  const tFilters = useTranslations("Audit.filters")
  const tActions = useTranslations("Audit.actionLabels")

  const columnLabels = React.useMemo<AuditColumnLabels>(
    () => ({
      timestamp: tCols("timestamp"),
      action: tCols("action"),
      product: tCols("product"),
      user: tCols("user"),
      ipAddress: tCols("ipAddress"),
      view: tCols("view"),
      system: tAudit("system"),
      emDash: tAudit("emDash"),
    }),
    [tCols, tAudit],
  )

  const columns = React.useMemo(
    () => getAuditColumns({ onViewDetails, labels: columnLabels }),
    [onViewDetails, columnLabels],
  )

  const actionOptions = React.useMemo(
    () => getAuditActionFilterOptions((action) => tActions(action)),
    [tActions],
  )

  const fakeActionColumn = React.useMemo(
    () =>
      ({
        id: "action",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => actionFilter,
        setFilterValue: (val: unknown) => {
          onActionFilterChange((val as string[] | undefined) ?? [])
        },
      }) as never,
    [actionFilter, onActionFilterChange],
  )

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      isLoading={isLoading}
      emptyMessage={tPage("empty")}
      filterContent={
        <div className="flex flex-wrap items-center gap-2">
          <DataTableFacetedFilter
            column={fakeActionColumn}
            title={tFilters("actionType")}
            options={actionOptions}
          />
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="h-8 w-[150px]"
            placeholder={tFilters("fromDate")}
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="h-8 w-[150px]"
            placeholder={tFilters("toDate")}
          />
        </div>
      }
    />
  )
}
