"use client"

import { useTranslations } from "next-intl"
import { AlertTriangleIcon, CheckCircleIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface LowStockBadgeProps {
  isLowStock: boolean
}

export function LowStockBadge({ isLowStock }: LowStockBadgeProps) {
  const t = useTranslations("Inventory")

  if (isLowStock) {
    return (
      <Badge variant="destructive">
        <AlertTriangleIcon data-icon="inline-start" />
        {t("stockRecords.badges.lowStock")}
      </Badge>
    )
  }

  return (
    <Badge variant="secondary">
      <CheckCircleIcon data-icon="inline-start" />
      {t("stockRecords.badges.ok")}
    </Badge>
  )
}
