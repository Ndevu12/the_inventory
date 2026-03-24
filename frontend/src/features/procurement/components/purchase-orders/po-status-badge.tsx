"use client"

import { useTranslations } from "next-intl"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { PurchaseOrderStatus } from "../../types/procurement.types"
import { PO_STATUS_COLOR_MAP } from "../../helpers/procurement-constants"

interface POStatusBadgeProps {
  status: PurchaseOrderStatus
  label?: string
  className?: string
}

export function POStatusBadge({ status, label, className }: POStatusBadgeProps) {
  const t = useTranslations("Procurement.poStatus")
  const colors = PO_STATUS_COLOR_MAP[status]
  const displayLabel = label ?? t(status)

  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        colors.bg,
        colors.text,
        className,
      )}
    >
      {displayLabel}
    </Badge>
  )
}
