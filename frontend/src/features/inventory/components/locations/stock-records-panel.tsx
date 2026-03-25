"use client"

import { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  LOCATION_STOCK_DRAWER_PAGE_SIZE,
  LOCATION_STOCK_PREVIEW_PAGE_SIZE,
  useLocationStockPage,
} from "../../hooks/use-locations"
import type { StockRecordAtLocation } from "../../types/location.types"

function StockLinesTable({ records }: { records: StockRecordAtLocation[] }) {
  const t = useTranslations("Inventory")

  return (
    <table className="w-full text-sm">
      <caption className="sr-only">{t("locations.subTableCaption")}</caption>
      <thead>
        <tr className="border-b bg-muted/50 text-left">
          <th className="px-4 py-2 font-medium">
            {t("locations.subTableProduct")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableQty")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableReserved")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableAvailable")}
          </th>
        </tr>
      </thead>
      <tbody>
        {records.map((r) => (
          <tr key={r.id} className="border-b last:border-0">
            <td className="px-4 py-2">
              <div className="font-medium">{r.product_name}</div>
              <div className="text-xs text-muted-foreground">
                {r.product_sku}
              </div>
            </td>
            <td className="px-4 py-2 text-right tabular-nums">{r.quantity}</td>
            <td className="px-4 py-2 text-right tabular-nums">
              {r.reserved_quantity}
            </td>
            <td className="px-4 py-2 text-right tabular-nums">
              <span
                className={cn(
                  r.is_low_stock && "font-medium text-destructive",
                )}
              >
                {r.available_quantity}
              </span>
              {r.is_low_stock && (
                <Badge variant="destructive" className="ml-2 text-[10px]">
                  {t("shared.low")}
                </Badge>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function StockRecordsPanel({
  locationId,
  locationName,
}: {
  locationId: number
  locationName?: string
}) {
  const t = useTranslations("Inventory")
  const [sheetOpen, setSheetOpen] = useState(false)
  const [drawerPage, setDrawerPage] = useState(1)

  const { data: preview, isLoading: previewLoading } = useLocationStockPage(
    locationId,
    { page: 1, page_size: LOCATION_STOCK_PREVIEW_PAGE_SIZE },
  )

  const { data: drawerPageData, isLoading: drawerLoading } =
    useLocationStockPage(
      locationId,
      { page: drawerPage, page_size: LOCATION_STOCK_DRAWER_PAGE_SIZE },
      { enabled: sheetOpen },
    )

  const onSheetOpenChange = (open: boolean) => {
    setSheetOpen(open)
    if (open) setDrawerPage(1)
  }

  const previewTotal = preview?.count ?? 0
  const previewShown = preview?.results.length ?? 0
  const hasMoreInLocation = previewTotal > previewShown

  const drawerPageSize = parseInt(LOCATION_STOCK_DRAWER_PAGE_SIZE, 10)
  const drawerTotal = drawerPageData?.count ?? 0
  const drawerTotalPages = Math.max(
    1,
    Math.ceil(drawerTotal / drawerPageSize),
  )

  const sheetTitle = useMemo(
    () =>
      locationName
        ? t("locations.stockSheetTitle", { name: locationName })
        : t("locations.stockSheetTitleFallback"),
    [locationName, t],
  )

  if (previewLoading) {
    return (
      <div className="space-y-2 px-4 py-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-full" />
        ))}
      </div>
    )
  }

  if (previewTotal === 0) {
    return (
      <p className="px-4 py-4 text-center text-sm text-muted-foreground">
        {t("locations.noStock")}
      </p>
    )
  }

  return (
    <div className="border-t">
      <div className="max-h-[min(24rem,55vh)] overflow-auto">
        <StockLinesTable records={preview?.results ?? []} />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t bg-muted/20 px-4 py-2 text-xs text-muted-foreground">
        <span>
          {t("locations.stockPreviewSummary", {
            shown: previewShown,
            total: previewTotal,
          })}
        </span>
        {hasMoreInLocation ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8"
            onClick={() => onSheetOpenChange(true)}
          >
            {t("locations.viewAllStock")}
          </Button>
        ) : null}
      </div>

      <Sheet open={sheetOpen} onOpenChange={onSheetOpenChange}>
        <SheetContent
          side="right"
          className="flex w-full flex-col gap-0 p-0 sm:max-w-2xl"
          showCloseButton
        >
          <SheetHeader className="border-b px-4 py-3">
            <SheetTitle>{sheetTitle}</SheetTitle>
            <SheetDescription>{t("locations.stockSheetDescription")}</SheetDescription>
          </SheetHeader>
          <div className="min-h-0 flex-1 overflow-auto px-0 py-2">
            {drawerLoading ? (
              <div className="space-y-2 px-4 py-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-7 w-full" />
                ))}
              </div>
            ) : (drawerPageData?.results.length ?? 0) === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                {t("locations.noStock")}
              </p>
            ) : (
              <StockLinesTable records={drawerPageData?.results ?? []} />
            )}
          </div>
          {drawerTotal > 0 ? (
            <div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t px-4 py-3">
              <p className="text-xs text-muted-foreground">
                {t("locations.stockPageOf", {
                  page: drawerPage,
                  totalPages: drawerTotalPages,
                })}
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={drawerPage <= 1 || drawerLoading}
                  onClick={() => setDrawerPage((p) => Math.max(1, p - 1))}
                >
                  {t("locations.stockPrevPage")}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={
                    drawerPage >= drawerTotalPages || drawerLoading
                  }
                  onClick={() =>
                    setDrawerPage((p) => Math.min(drawerTotalPages, p + 1))
                  }
                >
                  {t("locations.stockNextPage")}
                </Button>
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  )
}
