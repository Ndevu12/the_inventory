"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useStockValuation } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getStockValuationColumns } from "../helpers/report-columns"
import { VALUATION_METHOD_OPTIONS } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { SelectFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatCurrency, formatNumber } from "@/lib/utils/format"

export function StockValuationPage() {
  const { valuationMethod, setValuationMethod } = useReportFiltersStore()
  const { data, isLoading } = useStockValuation({ method: valuationMethod })
  const columns = React.useMemo(() => getStockValuationColumns(), [])

  const exportParams = React.useMemo(
    () => ({ method: valuationMethod }),
    [valuationMethod],
  )
  const { exporting, handleExport } = useExportReport("stock-valuation", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Stock Valuation"
        description="Inventory value by product using selected costing method"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label="Valuation Method"
          value={valuationMethod}
          onChange={(v) => setValuationMethod(v as typeof valuationMethod)}
          options={VALUATION_METHOD_OPTIONS}
          placeholder="Select method"
        />
      </div>

      {data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <SummaryCard label="Total Products" value={formatNumber(data.total_products)} />
          <SummaryCard label="Total Quantity" value={formatNumber(data.total_quantity)} />
          <SummaryCard label="Total Value" value={formatCurrency(Number(data.total_value))} />
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        emptyMessage="No stock valuation data."
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
