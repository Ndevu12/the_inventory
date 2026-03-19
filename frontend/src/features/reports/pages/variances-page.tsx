"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useVariances } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getVarianceColumns } from "../helpers/report-columns"
import { VARIANCE_TYPE_OPTIONS } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { SelectFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatNumber } from "@/lib/utils/format"
import type { VarianceType } from "../types/reports.types"

export function VariancesPage() {
  const { varianceType, setVarianceType } = useReportFiltersStore()

  const params = React.useMemo(
    () => ({
      variance_type: (varianceType || undefined) as VarianceType | undefined,
    }),
    [varianceType],
  )

  const { data, isLoading } = useVariances(params)
  const columns = React.useMemo(() => getVarianceColumns(), [])

  const exportParams = React.useMemo(
    () => ({
      ...(varianceType && { variance_type: varianceType }),
    }),
    [varianceType],
  )
  const { exporting, handleExport } = useExportReport("variances", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Variance Report"
        description="Inventory variances from cycle counts"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label="Variance Type"
          value={varianceType}
          onChange={setVarianceType}
          options={VARIANCE_TYPE_OPTIONS}
        />
      </div>

      {data?.summary && (
        <div className="grid gap-4 sm:grid-cols-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Total Variances</p>
              <p className="text-2xl font-semibold">{formatNumber(data.summary.total_variances)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Shortages</p>
              <p className="text-2xl font-semibold text-destructive">{formatNumber(data.summary.shortages)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Surpluses</p>
              <p className="text-2xl font-semibold text-amber-600 dark:text-amber-400">{formatNumber(data.summary.surpluses)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Net Variance</p>
              <p className="text-2xl font-semibold">
                {data.summary.net_variance > 0 ? "+" : ""}{formatNumber(data.summary.net_variance)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage="No variances found."
      />
    </div>
  )
}
