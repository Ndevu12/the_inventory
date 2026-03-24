"use client"

import { useTranslations } from "next-intl"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { CheckCircleIcon, XCircleIcon } from "lucide-react"

interface CanFulfillBadgeProps {
  canFulfill: boolean
  className?: string
}

export function CanFulfillBadge({ canFulfill, className }: CanFulfillBadgeProps) {
  const t = useTranslations("Sales.salesOrders.fulfillment")

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border-transparent font-medium",
        canFulfill
          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
          : "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
        className,
      )}
    >
      {canFulfill ? (
        <CheckCircleIcon className="size-3" />
      ) : (
        <XCircleIcon className="size-3" />
      )}
      {canFulfill ? t("canFulfill") : t("insufficientStock")}
    </Badge>
  )
}
