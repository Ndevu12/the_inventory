"use client"

import { useTranslations } from "next-intl"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SalesOrderStatus } from "../../types/sales.types"
import { SO_STATUS_COLOR_MAP } from "../../helpers/sales-constants"

interface SOStatusBadgeProps {
  status: SalesOrderStatus
  className?: string
}

export function SOStatusBadge({ status, className }: SOStatusBadgeProps) {
  const t = useTranslations("Sales.soStatus")
  const colors = SO_STATUS_COLOR_MAP[status]

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
      {t(status)}
    </Badge>
  )
}
