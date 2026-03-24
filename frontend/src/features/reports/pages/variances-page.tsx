"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useVariances } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getVarianceColumns } from "../helpers/report-columns"
import { VARIANCE_TYPE_VALUES } from "../helpers/report-constants"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { SelectFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"
import { formatNumber } from "@/lib/utils/format"
import type { VarianceType } from "../types/reports.types"

export function VariancesPage() {
  const tPage = useTranslations("Reports.pages.variances")
  const tFilters = useTranslations("Reports.filters")
  const tCol = useTranslations("Reports.columns")
  const tVar = useTranslations("Reports.options.variance")

  const { varianceType, setVarianceType } = useReportFiltersStore()

  const varianceOptions = React.useMemo(
    () =>
      VARIANCE_TYPE_VALUES.map((value) => ({
        value,
        label: tVar(value),
      })),
    [tVar],
  )

  const columns = React.useMemo(
    () => getVarianceColumns((k) => tCol(k)),
    [tCol],
  )

  const params = React.useMemo(
    () => ({
      variance_type: (varianceType || undefined) as VarianceType | undefined,
    }),
    [varianceType],
  )

  const { data, isLoading } = useVariances(params)

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
        title={tPage("title")}
        description={tPage("description")}
        actions={<ExportButtons onExport={handleExport} exporting={exporting} />}
      />

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label={tFilters("varianceType")}
          value={varianceType}
          onChange={setVarianceType}
          options={varianceOptions}
        />
      </div>

      {data?.summary && (
        <div className="grid gap-4 sm:grid-cols-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("totalVariances")}</p>
              <p className="text-2xl font-semibold">{formatNumber(data.summary.total_variances)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("shortages")}</p>
              <p className="text-2xl font-semibold text-destructive">{formatNumber(data.summary.shortages)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("surpluses")}</p>
              <p className="text-2xl font-semibold text-amber-600 dark:text-amber-400">{formatNumber(data.summary.surpluses)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("netVariance")}</p>
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
        emptyMessage={tPage("empty")}
      />
    </div>
  )
}
