"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useMovementHistory } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getMovementHistoryColumns } from "../helpers/report-columns"
import { MOVEMENT_TYPE_VALUES } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { DateRangeFilter, SelectFilter } from "../components/report-filters"

export function MovementHistoryPage() {
  const tPage = useTranslations("Reports.pages.movementHistory")
  const tFilters = useTranslations("Reports.filters")
  const tCol = useTranslations("Reports.columns")
  const tMov = useTranslations("Reports.options.movement")

  const { dateFrom, dateTo, movementType, setDateFrom, setDateTo, setMovementType } =
    useReportFiltersStore()

  const movementOptions = React.useMemo(
    () =>
      MOVEMENT_TYPE_VALUES.map((value) => ({
        value,
        label: tMov(value),
      })),
    [tMov],
  )

  const columns = React.useMemo(
    () =>
      getMovementHistoryColumns(
        (k) => tCol(k),
        (type) => tMov(type),
      ),
    [tCol, tMov],
  )

  const params = React.useMemo(
    () => ({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      type: movementType || undefined,
    }),
    [dateFrom, dateTo, movementType],
  )

  const { data, isLoading } = useMovementHistory(params)

  const exportParams = React.useMemo(
    () => ({
      ...(dateFrom && { date_from: dateFrom }),
      ...(dateTo && { date_to: dateTo }),
      ...(movementType && { type: movementType }),
    }),
    [dateFrom, dateTo, movementType],
  )
  const { exporting, handleExport } = useExportReport("movement-history", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <DateRangeFilter
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
        />
        <SelectFilter
          label={tFilters("movementType")}
          value={movementType}
          onChange={setMovementType}
          options={movementOptions}
        />
      </div>

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage={tPage("empty")}
      />
    </div>
  )
}
