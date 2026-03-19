"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { DataTable } from "@/components/data-table/data-table"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { Input } from "@/components/ui/input"
import { AUDIT_ACTION_OPTIONS } from "../helpers/audit-constants"
import type { AuditEntry } from "../types/audit.types"
import { getAuditColumns } from "./audit-columns"

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
  const columns = React.useMemo(
    () => getAuditColumns({ onViewDetails }),
    [onViewDetails],
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
      emptyMessage="No audit log entries found."
      filterContent={
        <div className="flex flex-wrap items-center gap-2">
          <DataTableFacetedFilter
            column={fakeActionColumn}
            title="Action Type"
            options={AUDIT_ACTION_OPTIONS}
          />
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="h-8 w-[150px]"
            placeholder="From date"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="h-8 w-[150px]"
            placeholder="To date"
          />
        </div>
      }
    />
  )
}
