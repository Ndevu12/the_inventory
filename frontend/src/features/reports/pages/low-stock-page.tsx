"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useLowStock } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { getLowStockColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"

export function LowStockPage() {
  const { data, isLoading } = useLowStock()
  const columns = React.useMemo(() => getLowStockColumns(), [])
  const { exporting, handleExport } = useExportReport("low-stock")

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Low Stock Report"
        description="Products at or below their reorder point"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage="No low-stock products. All stock levels are healthy."
      />
    </div>
  )
}
