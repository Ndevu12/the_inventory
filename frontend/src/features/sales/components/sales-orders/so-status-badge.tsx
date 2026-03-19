"use client"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SalesOrderStatus } from "../../types/sales.types"
import { SO_STATUS_COLOR_MAP } from "../../helpers/sales-constants"

interface SOStatusBadgeProps {
  status: SalesOrderStatus
  label?: string
  className?: string
}

export function SOStatusBadge({ status, label, className }: SOStatusBadgeProps) {
  const colors = SO_STATUS_COLOR_MAP[status]
  const displayLabel = label ?? status.charAt(0).toUpperCase() + status.slice(1)

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
