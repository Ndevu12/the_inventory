"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useOverstock } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getOverstockColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { NumberFilter } from "../components/report-filters"

export function OverstockPage() {
  const tPage = useTranslations("Reports.pages.overstock")
  const tFilters = useTranslations("Reports.filters")
  const tCol = useTranslations("Reports.columns")

  const { threshold, setThreshold } = useReportFiltersStore()
  const { data, isLoading } = useOverstock({ threshold })
  const columns = React.useMemo(
    () => getOverstockColumns((k) => tCol(k)),
    [tCol],
  )

  const exportParams = React.useMemo(
    () => ({ threshold: String(threshold) }),
    [threshold],
  )
  const { exporting, handleExport } = useExportReport("overstock", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <NumberFilter
          label={tFilters("thresholdMultiplier")}
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
        emptyMessage={tPage("empty")}
      />
    </div>
  )
}
