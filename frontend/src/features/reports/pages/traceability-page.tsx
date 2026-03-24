"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { useTraceability } from "../hooks/use-reports"
import { useExportReport } from "../hooks/use-export-report"
import { useReportFiltersStore } from "../stores/report-filters-store"
import { getTraceabilityColumns } from "../helpers/report-columns"
import { ReportTable } from "../components/report-table"
import { ExportButtons } from "../components/export-buttons"
import { TextFilter } from "../components/report-filters"
import { Card, CardContent } from "@/components/ui/card"

export function TraceabilityPage() {
  const tPage = useTranslations("Reports.pages.traceability")
  const tFilters = useTranslations("Reports.filters")
  const tCol = useTranslations("Reports.columns")

  const { productSku, lotNumber, setProductSku, setLotNumber } =
    useReportFiltersStore()

  const canQuery = !!productSku && !!lotNumber

  const { data, isLoading } = useTraceability({
    product: productSku,
    lot: lotNumber,
  })

  const columns = React.useMemo(
    () => getTraceabilityColumns((k) => tCol(k)),
    [tCol],
  )

  const exportParams = React.useMemo(
    () => ({
      product: productSku,
      lot: lotNumber,
    }),
    [productSku, lotNumber],
  )
  const { exporting, handleExport } = useExportReport("product-traceability", exportParams)

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tPage("title")}
        description={tPage("description")}
        actions={
          canQuery ? (
            <ExportButtons onExport={handleExport} exporting={exporting} />
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-end gap-3">
        <TextFilter
          label={tFilters("productSku")}
          value={productSku}
          onChange={setProductSku}
          placeholder={tPage("placeholderSku")}
        />
        <TextFilter
          label={tFilters("lotNumber")}
          value={lotNumber}
          onChange={setLotNumber}
          placeholder={tPage("placeholderLot")}
        />
      </div>

      {!canQuery && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {tPage("promptEnterSkuAndLot")}
          </CardContent>
        </Card>
      )}

      {canQuery && data?.product && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("productLabel")}</p>
              <p className="text-lg font-semibold">{data.product.name}</p>
              <p className="text-sm text-muted-foreground">{data.product.sku}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{tPage("lotLabel")}</p>
              <p className="text-lg font-semibold">{data.lot.lot_number}</p>
              {data.lot.expiry_date && (
                <p className="text-sm text-muted-foreground">
                  {tPage("expiresWithDate", { date: data.lot.expiry_date })}
                </p>
              )}
              {data.lot.supplier && (
                <p className="text-sm text-muted-foreground">
                  {tPage("supplierWithName", { name: data.lot.supplier })}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {canQuery && (
        <ReportTable
          columns={columns}
          data={data?.chain ?? []}
          isLoading={isLoading}
          emptyMessage={tPage("empty")}
        />
      )}
    </div>
  )
}
