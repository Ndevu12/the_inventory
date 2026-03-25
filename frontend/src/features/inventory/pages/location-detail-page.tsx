"use client"

import { use, useState } from "react"
import { useTranslations } from "next-intl"
import { Link } from "@/i18n/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { CapacityBar } from "../components/locations/capacity-bar"
import { StockLinesTable } from "../components/locations/stock-records-panel"
import {
  LOCATION_STOCK_DRAWER_PAGE_SIZE,
  useLocation,
  useLocationStockPage,
} from "../hooks/use-locations"

interface LocationDetailPageProps {
  params: Promise<{ id: string }>
}

function LocationDetailInvalidId() {
  const t = useTranslations("Inventory")
  return (
    <div className="space-y-6">
      <PageHeader title={t("locations.detail.invalidTitle")} />
      <p className="text-muted-foreground">
        {t("locations.detail.invalidBody")}
      </p>
      <Button variant="outline" asChild>
        <Link href="/stock/locations">
          <ArrowLeftIcon className="mr-2 size-4" />
          {t("locations.detail.backToList")}
        </Link>
      </Button>
    </div>
  )
}

function LocationDetailContent({ locationId }: { locationId: number }) {
  const t = useTranslations("Inventory")
  const { data: location, isLoading, isError } = useLocation(locationId)

  const [stockPage, setStockPage] = useState(1)
  const { data: stockPageData, isLoading: stockLoading } = useLocationStockPage(
    locationId,
    { page: stockPage, page_size: LOCATION_STOCK_DRAWER_PAGE_SIZE },
  )

  const pageSize = parseInt(LOCATION_STOCK_DRAWER_PAGE_SIZE, 10)
  const stockTotal = stockPageData?.count ?? 0
  const stockTotalPages = Math.max(1, Math.ceil(stockTotal / pageSize))

  if (isLoading && !location) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full max-w-xl" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isError || !location) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("locations.detail.notFoundTitle")} />
        <p className="text-muted-foreground">
          {t("locations.detail.notFoundBody")}
        </p>
        <Button variant="outline" asChild>
          <Link href="/stock/locations">
            <ArrowLeftIcon className="mr-2 size-4" />
            {t("locations.detail.backToList")}
          </Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start gap-4">
        <Button variant="ghost" size="sm" className="-ml-2" asChild>
          <Link href="/stock/locations">
            <ArrowLeftIcon className="mr-1 size-4" />
            {t("locations.detail.backToList")}
          </Link>
        </Button>
      </div>

      <PageHeader
        title={location.name}
        description={location.description || undefined}
        actions={
          <Badge variant={location.is_active ? "default" : "secondary"}>
            {location.is_active ? t("shared.active") : t("shared.inactive")}
          </Badge>
        }
      />

      <Card className="max-w-xl">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {location.warehouse?.name ?? t("locations.detail.retailSite")}
          </CardTitle>
          <CardDescription>{t("locations.detail.capacityHint")}</CardDescription>
        </CardHeader>
        <CardContent>
          <CapacityBar
            currentUtilization={location.current_utilization}
            maxCapacity={location.max_capacity}
          />
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">
          {t("locations.detail.stockSectionTitle")}
        </h2>
        <div className="rounded-md border">
          {stockLoading && !stockPageData ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : stockTotal === 0 ? (
            <p className="p-8 text-center text-sm text-muted-foreground">
              {t("locations.noStock")}
            </p>
          ) : (
            <StockLinesTable records={stockPageData?.results ?? []} />
          )}
        </div>
        {stockTotal > 0 ? (
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <p>
              {t("locations.stockPageOf", {
                page: stockPage,
                totalPages: stockTotalPages,
              })}
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={stockPage <= 1 || stockLoading}
                onClick={() => setStockPage((p) => Math.max(1, p - 1))}
              >
                {t("locations.stockPrevPage")}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={stockPage >= stockTotalPages || stockLoading}
                onClick={() =>
                  setStockPage((p) => Math.min(stockTotalPages, p + 1))
                }
              >
                {t("locations.stockNextPage")}
              </Button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  )
}

export function LocationDetailPage({ params }: LocationDetailPageProps) {
  const { id } = use(params)
  const locationId = Number(id)
  const invalidId = !Number.isFinite(locationId) || locationId <= 0

  if (invalidId) {
    return <LocationDetailInvalidId />
  }

  return <LocationDetailContent key={id} locationId={locationId} />
}
