"use client"

import * as React from "react"
import { PageHeader } from "@/components/layout/page-header"
import { useProductExpiry } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getProductExpiryColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { NumberFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatNumber } from "@/lib/utils/format"

export function ProductExpiryPage() {
  const { daysAhead, setDaysAhead } = useReportFiltersStore()
  const { data, isLoading } = useProductExpiry({ days_ahead: daysAhead })
  const columns = React.useMemo(() => getProductExpiryColumns(), [])

  const exportParams = React.useMemo(
    () => ({ days_ahead: String(daysAhead) }),
    [daysAhead],
  )
  const { exporting, handleExport } = useExportReport("product-expiry", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Product Expiry Report"
        description="Lots expiring soon or already expired"
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <NumberFilter
          label="Look-ahead (days)"
          value={daysAhead}
          onChange={setDaysAhead}
          min={1}
          max={365}
        />
      </div>

      {data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Expired</p>
              <p className="text-2xl font-semibold text-destructive">
                {formatNumber(data.expired_count)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Expiring Soon</p>
              <p className="text-2xl font-semibold text-amber-600 dark:text-amber-400">
                {formatNumber(data.expiring_count)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">Total Lots</p>
              <p className="text-2xl font-semibold">
                {formatNumber(data.expired_count + data.expiring_count)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <ReportTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyMessage="No expiring or expired lots."
      />
    </div>
  )
}
