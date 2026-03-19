"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useOverstock } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getOverstockColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { NumberFilter } from "../components/report-filters"

export function OverstockPage() {
  const { threshold, setThreshold } = useReportFiltersStore()
  const { data, isLoading } = useOverstock({ threshold })
  const columns = React.useMemo(() => getOverstockColumns(), [])

  const exportParams = React.useMemo(
    () => ({ threshold: String(threshold) }),
    [threshold],
  )
  const { exporting, handleExport } = useExportReport("overstock", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Overstock Report"
        description="Products exceeding their reorder point by the threshold multiplier"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <NumberFilter
          label="Threshold Multiplier"
          value={threshold}
          onChange={setThreshold}
          min={1}
          max={100}
        />
      </div>

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage="No overstocked products."
      />
    </div>
  )
}
