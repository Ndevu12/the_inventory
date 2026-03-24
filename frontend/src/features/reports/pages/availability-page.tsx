"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useAvailability } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { getAvailabilityColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { Card, CardContent } from "@/components/ui/card"
import { formatCurrency } from "@/lib/utils/format"

export function AvailabilityPage() {
  const tPage = useTranslations("Reports.pages.availability")
  const tCol = useTranslations("Reports.columns")

  const { data, isLoading } = useAvailability()
  const columns = React.useMemo(
    () => getAvailabilityColumns((k) => tCol(k)),
    [tCol],
  )
  const { exporting, handleExport } = useExportReport("availability")

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      {data && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("products")}</p>
              <p className="text-2xl font-semibold">{data.count}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("totalReservedValue")}</p>
              <p className="text-2xl font-semibold">{formatCurrency(Number(data.total_reserved_value))}</p>
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
