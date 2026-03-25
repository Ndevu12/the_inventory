"use client"

import { useCallback, useDeferredValue, useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { PlusIcon, SearchIcon } from "lucide-react"
import { Link, useRouter } from "@/i18n/navigation"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useInfiniteLocations } from "../hooks/use-locations"
import {
  useWarehouseQuickStats,
  useWarehousesForSelect,
} from "../hooks/use-warehouses"
import { LocationTree } from "../components/locations/location-tree"
import { LocationSavedViewsToolbar } from "../components/locations/location-saved-views-toolbar"
import type { LocationSavedView } from "../components/locations/location-saved-views-toolbar"
import { WarehouseSummaryStrip } from "../components/locations/warehouse-summary-strip"
import { LocationFormDialog } from "../components/locations/location-form-dialog"
import type { StockLocation } from "../types/location.types"

const FOCUS_QUERY = "focus"

export function LocationListPage() {
  const t = useTranslations("Inventory")
  const tCommon = useTranslations("Common")
  const router = useRouter()
  const searchParams = useSearchParams()

  const [search, setSearch] = useState("")
  const [warehouseFilter, setWarehouseFilter] = useState<string>("__all__")
  const deferredSearch = useDeferredValue(search)

  const focusParam = searchParams.get(FOCUS_QUERY)
  const focusIdParsed = focusParam ? Number.parseInt(focusParam, 10) : NaN
  const focusIdFromUrl =
    focusParam != null && focusParam !== "" && Number.isFinite(focusIdParsed)
      ? focusIdParsed
      : null

  const { data: warehouses = [] } = useWarehousesForSelect()
  const showFacilityStrip = warehouses.length > 0
  const { data: warehouseQuickStats, isLoading: isWarehouseStatsLoading } =
    useWarehouseQuickStats(showFacilityStrip)

  const warehouseFilterItems = useMemo(
    () => [
      { value: "__all__", label: t("locations.filter.allSites") },
      { value: "__retail__", label: t("locations.filter.retailOnly") },
      ...warehouses.map((w) => ({ value: String(w.id), label: w.name })),
    ],
    [warehouses, t],
  )

  const params = useMemo(() => {
    const p: Record<string, string> = {}
    if (deferredSearch) p.search = deferredSearch
    if (warehouseFilter === "__retail__") p.warehouse__isnull = "true"
    else if (warehouseFilter !== "__all__") p.warehouse = warehouseFilter
    return p
  }, [deferredSearch, warehouseFilter])

  const {
    data,
    isPending,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage: fetchNextLocationsPage,
  } = useInfiniteLocations(params)

  const locations = useMemo(
    () => data?.pages.flatMap((p) => p.results) ?? [],
    [data],
  )
  const totalCount = data?.pages[0]?.count
  const isLoading = isPending && !data

  useEffect(() => {
    if (focusIdFromUrl == null) return
    router.replace(`/stock/locations/${focusIdFromUrl}`)
  }, [focusIdFromUrl, router])

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingLocation, setEditingLocation] =
    useState<StockLocation | null>(null)

  const openCreate = () => {
    setEditingLocation(null)
    setDialogOpen(true)
  }

  const openEdit = (loc: StockLocation) => {
    setEditingLocation(loc)
    setDialogOpen(true)
  }

  const applySavedView = useCallback((view: LocationSavedView) => {
    setSearch(view.search)
    setWarehouseFilter(view.warehouseFilter)
  }, [])

  const showSiteGroups = warehouseFilter === "__all__"

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("locations.title")}
        description={t("locations.description")}
        actions={
          <Button onClick={openCreate}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("locations.addLocation")}
          </Button>
        }
      />

      {!showFacilityStrip ? (
        <div className="rounded-lg border border-dashed bg-muted/30 p-4 text-sm">
          <p className="font-medium text-foreground">
            {t("locations.noFacilitiesCalloutTitle")}
          </p>
          <p className="mt-1 text-muted-foreground">
            {t("locations.noFacilitiesCalloutBody")}
          </p>
          <Button variant="link" asChild className="mt-2 h-auto px-0 text-sm">
            <Link href="/stock/warehouses">
              {t("locations.noFacilitiesCalloutLink")}
            </Link>
          </Button>
        </div>
      ) : null}

      {showFacilityStrip ? (
        <WarehouseSummaryStrip
          warehouses={warehouses}
          quickStats={warehouseQuickStats}
          isLoadingStats={isWarehouseStatsLoading}
          activeFilter={warehouseFilter}
        />
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-end">
          <div className="relative max-w-sm flex-1">
            <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t("locations.searchPlaceholder")}
              aria-label={tCommon("searchAria")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="w-full max-w-xs space-y-2">
            <Label htmlFor="loc-wh-filter">{t("locations.filter.label")}</Label>
            <Select
              items={warehouseFilterItems}
              value={warehouseFilter}
              onValueChange={(v) => v && setWarehouseFilter(v)}
            >
              <SelectTrigger id="loc-wh-filter" className="w-full">
                <SelectValue placeholder={t("locations.filter.label")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">
                  {t("locations.filter.allSites")}
                </SelectItem>
                <SelectItem value="__retail__">
                  {t("locations.filter.retailOnly")}
                </SelectItem>
                {warehouses.map((w) => (
                  <SelectItem key={w.id} value={String(w.id)}>
                    {w.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="shrink-0 self-end sm:self-auto">
          <LocationSavedViewsToolbar
            search={search}
            warehouseFilter={warehouseFilter}
            onApplyView={applySavedView}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {t("locations.hierarchy.hintCommandPalette")}
      </p>

      <LocationTree
        locations={locations}
        hasWarehouses={showFacilityStrip}
        showSiteGroups={showSiteGroups}
        onEdit={openEdit}
        isLoading={isLoading}
        hasNextPage={Boolean(hasNextPage)}
        isFetchingNextPage={isFetchingNextPage}
        fetchNextPage={() => {
          void fetchNextLocationsPage()
        }}
        totalCount={totalCount}
      />

      <LocationFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        location={editingLocation}
      />
    </div>
  )
}
