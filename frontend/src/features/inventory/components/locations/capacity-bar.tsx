"use client"

import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

interface CapacityBarProps {
  currentUtilization: number
  maxCapacity: number | null
  className?: string
}

function utilizationColor(pct: number) {
  if (pct < 50) return "bg-emerald-500"
  if (pct < 80) return "bg-amber-500"
  return "bg-red-500"
}

export function CapacityBar({
  currentUtilization,
  maxCapacity,
  className,
}: CapacityBarProps) {
  const t = useTranslations("Inventory")
  const tCap = useTranslations("Inventory.locations.capacity")

  if (maxCapacity === null) {
    return (
      <div
        className={cn(
          "flex items-center gap-1.5 text-xs text-muted-foreground",
          className,
        )}
        role="status"
        aria-label={tCap("unlimitedMeterAria", {
          count: currentUtilization,
        })}
      >
        <span className="tabular-nums font-medium text-foreground" aria-hidden>
          {currentUtilization}
        </span>
        <span aria-hidden>{t("shared.capacityUnlimited")}</span>
      </div>
    )
  }

  const pct =
    maxCapacity > 0
      ? Math.min((currentUtilization / maxCapacity) * 100, 100)
      : 0
  const pctRounded = Math.round(pct)

  return (
    <div
      className={cn("space-y-1", className)}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={maxCapacity}
      aria-valuenow={currentUtilization}
      aria-label={tCap("meterAria", {
        pct: pctRounded,
        current: currentUtilization,
        max: maxCapacity,
      })}
    >
      <div
        className="flex justify-between text-xs text-muted-foreground"
        aria-hidden
      >
        <span className="tabular-nums">
          {tCap("ofMax", {
            current: currentUtilization,
            max: maxCapacity,
          })}
        </span>
        <span className="tabular-nums">
          {tCap("percent", { pct: pctRounded })}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            utilizationColor(pct),
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
