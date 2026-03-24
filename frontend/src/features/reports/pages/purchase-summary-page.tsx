"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { usePurchaseSummary } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getPeriodSummaryColumns } from "../helpers/report-columns"
import { REPORT_PERIOD_VALUES } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { DateRangeFilter, SelectFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatCurrency, formatNumber } from "@/lib/utils/format"

export function PurchaseSummaryPage() {
  const tPage = useTranslations("Reports.pages.purchaseSummary")
  const tFilters = useTranslations("Reports.filters")
  const tShared = useTranslations("Reports.shared")
  const tPer = useTranslations("Reports.options.period")
  const tCol = useTranslations("Reports.columns")

  const { dateFrom, dateTo, period, setDateFrom, setDateTo, setPeriod } =
    useReportFiltersStore()

  const periodOptions = React.useMemo(
    () =>
      REPORT_PERIOD_VALUES.map((value) => ({
        value,
        label: tPer(value),
      })),
    [tPer],
  )

  const columns = React.useMemo(
    () => getPeriodSummaryColumns((k) => tCol(k), "totalCost"),
    [tCol],
  )

  const params = React.useMemo(
    () => ({
      period,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [period, dateFrom, dateTo],
  )

  const { data, isLoading } = usePurchaseSummary(params)

  const exportParams = React.useMemo(
    () => ({
      period,
      ...(dateFrom && { date_from: dateFrom }),
      ...(dateTo && { date_to: dateTo }),
    }),
    [period, dateFrom, dateTo],
  )
  const { exporting, handleExport } = useExportReport("purchase-summary", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label={tFilters("period")}
          value={period}
          onChange={(v) => setPeriod(v as typeof period)}
          options={periodOptions}
          placeholder={tShared("selectPeriod")}
        />
        <DateRangeFilter
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
        />
      </div>

      {data?.totals && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("totalOrders")}</p>
              <p className="text-2xl font-semibold">{formatNumber(data.totals.total_orders)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("totalCost")}</p>
              <p className="text-2xl font-semibold">{formatCurrency(Number(data.totals.total_cost))}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage={tPage("empty")}
      />
    </div>
  )
}
