"use client"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { PurchaseOrderStatus } from "../../types/procurement.types"
import { PO_STATUS_COLOR_MAP, PO_STATUS_MAP } from "../../helpers/procurement-constants"

interface POStatusBadgeProps {
  status: PurchaseOrderStatus
  label?: string
  className?: string
}

export function POStatusBadge({ status, label, className }: POStatusBadgeProps) {
  const colors = PO_STATUS_COLOR_MAP[status]
  const displayLabel = label ?? PO_STATUS_MAP[status] ?? status

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
