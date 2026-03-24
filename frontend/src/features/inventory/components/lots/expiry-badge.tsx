"use client"

import { useTranslations } from "next-intl"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface ExpiryBadgeProps {
  daysToExpiry: number | null
  isExpired: boolean
  className?: string
}

function expiryClassName(
  daysToExpiry: number | null,
  isExpired: boolean,
): string {
  if (isExpired || (daysToExpiry !== null && daysToExpiry <= 0)) {
    return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
  }

  if (daysToExpiry === null) {
    return "bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400"
  }

  if (daysToExpiry <= 30) {
    return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
  }

  if (daysToExpiry <= 90) {
    return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
  }

  return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
}

export function ExpiryBadge({
  daysToExpiry,
  isExpired,
  className,
}: ExpiryBadgeProps) {
  const t = useTranslations("Inventory")

  let label: string
  if (isExpired || (daysToExpiry !== null && daysToExpiry <= 0)) {
    label = t("lots.expiry.expired")
  } else if (daysToExpiry === null) {
    label = t("lots.expiry.noExpiry")
  } else {
    label = t("lots.expiry.daysLeft", { days: daysToExpiry })
  }

  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        expiryClassName(daysToExpiry, isExpired),
        className,
      )}
    >
      {label}
    </Badge>
  )
}
