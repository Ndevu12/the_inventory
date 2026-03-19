"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useAvailability } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { getAvailabilityColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { Card, CardContent } from "@/components/ui/card"
import { formatCurrency } from "@/lib/utils/format"

export function AvailabilityPage() {
  const { data, isLoading } = useAvailability()
  const columns = React.useMemo(() => getAvailabilityColumns(), [])
  const { exporting, handleExport } = useExportReport("availability")

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Availability Report"
        description="Per-product stock, reserved, and available quantities"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      {data && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Products</p>
              <p className="text-2xl font-semibold">{data.count}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Total Reserved Value</p>
              <p className="text-2xl font-semibold">{formatCurrency(Number(data.total_reserved_value))}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage="No availability data."
      />
    </div>
  )
}
