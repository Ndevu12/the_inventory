"use client"

import { useMemo, type ReactNode } from "react"
import { AlertTriangleIcon, WarehouseIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { formatCompactNumber } from "@/features/dashboard/helpers/chart-helpers"
import type { WarehouseQuickStats } from "../../types/warehouse.types"

export interface WarehouseSummaryStripProps {
  warehouses: { id: number; name: string }[]
  quickStats: WarehouseQuickStats[] | undefined
  isLoadingStats: boolean
  /** Mirrors Site scope (read-only); highlights the card that matches the active filter. */
  activeFilter: string
}

export function WarehouseSummaryStrip({
  warehouses,
  quickStats,
  isLoadingStats,
  activeFilter,
}: WarehouseSummaryStripProps) {
  const t = useTranslations("Inventory.locations.warehouseStrip")
  const locale = useLocale()

  const statsById = useMemo(() => {
    const m = new Map<number, WarehouseQuickStats>()
    for (const row of quickStats ?? []) {
      m.set(row.id, row)
    }
    return m
  }, [quickStats])

  return (
    <div
      className="-mx-1 flex snap-x snap-mandatory gap-4 overflow-x-auto px-1 pb-1 [-ms-overflow-style:none] [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5"
      role="list"
    >
      {warehouses.map((w) => {
        const row = statsById.get(w.id)
        const highlighted = activeFilter === String(w.id)
        return (
          <StripCard
            key={w.id}
            highlighted={highlighted}
            ariaLabel={t("cardAriaSite", { name: w.name })}
          >
            {isLoadingStats ? (
              <>
                <CardHeader className="space-y-1 pb-3">
                  <div className="flex items-start gap-2.5">
                    <div
                      className={cn(
                        "flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted/80 text-muted-foreground",
                        highlighted && "bg-primary/10 text-primary",
                      )}
                      aria-hidden
                    >
                      <WarehouseIcon className="size-4" />
                    </div>
                    <div className="min-w-0 flex-1 space-y-2">
                      <CardTitle className="truncate text-sm leading-snug font-semibold">
                        {w.name}
                      </CardTitle>
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <Skeleton className="h-10 w-24" />
                  <Skeleton className="h-[4.25rem] w-full rounded-lg" />
                  <Skeleton className="h-5 w-32" />
                </CardContent>
              </>
            ) : !row ? (
              <>
                <CardHeader className="pb-2">
                  <div className="flex items-start gap-2.5">
                    <div
                      className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted/80 text-muted-foreground"
                      aria-hidden
                    >
                      <WarehouseIcon className="size-4" />
                    </div>
                    <CardTitle className="truncate text-sm leading-snug font-semibold">
                      {w.name}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-muted-foreground text-xs">{t("noStats")}</p>
                </CardContent>
              </>
            ) : (
              <>
                <CardHeader className="space-y-1 pb-3">
                  <div className="flex items-start gap-2.5">
                    <div
                      className={cn(
                        "flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted/80 text-muted-foreground",
                        highlighted && "bg-primary/10 text-primary",
                      )}
                      aria-hidden
                    >
                      <WarehouseIcon className="size-4" />
                    </div>
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <CardTitle className="truncate text-sm leading-snug font-semibold">
                        {w.name}
                      </CardTitle>
                      <CardDescription className="text-xs leading-normal">
                        {t("locationsCount", { count: row.location_count })}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div>
                    <p className="text-muted-foreground mb-0.5 text-[11px] font-medium tracking-wide uppercase">
                      {t("onHand")}
                    </p>
                    <p className="text-foreground text-xl font-semibold leading-none tabular-nums tracking-tight">
                      {formatCompactNumber(row.total_on_hand, locale)}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted/45 px-2.5 py-2">
                    <div className="min-w-0 space-y-0.5">
                      <p className="text-muted-foreground text-[11px] leading-none">
                        {t("available")}
                      </p>
                      <p className="text-foreground text-sm font-medium tabular-nums leading-none">
                        {formatCompactNumber(row.available_quantity, locale)}
                      </p>
                    </div>
                    <div className="min-w-0 space-y-0.5 border-s border-foreground/10 ps-2.5">
                      <p className="text-muted-foreground text-[11px] leading-none">
                        {t("reserved")}
                      </p>
                      <p className="text-foreground text-sm font-medium tabular-nums leading-none">
                        {formatCompactNumber(row.reserved_quantity, locale)}
                      </p>
                    </div>
                  </div>

                  {row.utilization_percent != null ? (
                    <div className="space-y-1.5">
                      <div className="text-muted-foreground flex items-baseline justify-between gap-2 text-[11px]">
                        <span className="truncate">
                          {t("utilization", {
                            pct: row.utilization_percent,
                          })}
                        </span>
                      </div>
                      <div
                        className="bg-muted h-1.5 overflow-hidden rounded-full"
                        role="presentation"
                        aria-hidden
                      >
                        <div
                          className="h-full rounded-full bg-primary/85 transition-[width] duration-300"
                          style={{
                            width: `${Math.min(Math.max(row.utilization_percent, 0), 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ) : null}

                  {row.low_stock_line_count > 0 ? (
                    <div className="border-border/60 flex items-center gap-1.5 border-t pt-2">
                      <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-1.5 py-0.5 text-[11px] font-medium text-amber-700 dark:text-amber-400">
                        <AlertTriangleIcon className="size-3 shrink-0" aria-hidden />
                        {t("lowStockLines", {
                          count: row.low_stock_line_count,
                        })}
                      </span>
                    </div>
                  ) : null}
                </CardContent>
              </>
            )}
          </StripCard>
        )
      })}
    </div>
  )
}

function StripCard({
  highlighted,
  ariaLabel,
  children,
}: {
  highlighted: boolean
  ariaLabel: string
  children: ReactNode
}) {
  return (
    <div
      role="listitem"
      aria-label={ariaLabel}
      className={cn(
        "w-[min(100%,17.5rem)] min-w-[15.5rem] shrink-0 snap-start text-left outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        highlighted && "relative z-[1]",
      )}
    >
      <Card
        size="sm"
        className={cn(
          "h-full gap-0 py-0 transition-[box-shadow,background-color]",
          highlighted
            ? "bg-primary/[0.04] ring-2 ring-primary shadow-sm dark:bg-primary/10"
            : "ring-1 ring-foreground/10 hover:bg-muted/25",
        )}
      >
        {children}
      </Card>
    </div>
  )
}
