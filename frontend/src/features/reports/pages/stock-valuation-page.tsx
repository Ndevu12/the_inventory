"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useStockValuation } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getStockValuationColumns } from "../helpers/report-columns"
import { VALUATION_METHOD_VALUES } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { SelectFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatCurrency, formatNumber } from "@/lib/utils/format"

export function StockValuationPage() {
  const tPage = useTranslations("Reports.pages.stockValuation")
  const tFilters = useTranslations("Reports.filters")
  const tShared = useTranslations("Reports.shared")
  const tOptVal = useTranslations("Reports.options.valuation")
  const tCol = useTranslations("Reports.columns")

  const { valuationMethod, setValuationMethod } = useReportFiltersStore()
  const { data, isLoading } = useStockValuation({ method: valuationMethod })

  const valuationOptions = React.useMemo(
    () =>
      VALUATION_METHOD_VALUES.map((value) => ({
        value,
        label: tOptVal(value),
      })),
    [tOptVal],
  )

  const columns = React.useMemo(
    () => getStockValuationColumns((k) => tCol(k)),
    [tCol],
  )

  const exportParams = React.useMemo(
    () => ({ method: valuationMethod }),
    [valuationMethod],
  )
  const { exporting, handleExport } = useExportReport("stock-valuation", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label={tFilters("valuationMethod")}
          value={valuationMethod}
          onChange={(v) => setValuationMethod(v as typeof valuationMethod)}
          options={valuationOptions}
          placeholder={tShared("selectMethod")}
        />
      </div>

      {data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <SummaryCard label={tPage("summaryTotalProducts")} value={formatNumber(data.total_products)} />
          <SummaryCard label={tPage("summaryTotalQuantity")} value={formatNumber(data.total_quantity)} />
          <SummaryCard label={tPage("summaryTotalValue")} value={formatCurrency(Number(data.total_value))} />
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        emptyMessage={tPage("empty")}
      />
    </div>
  )
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  )
}
