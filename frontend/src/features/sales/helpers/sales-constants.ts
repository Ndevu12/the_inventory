import type { FacetedFilterOption } from "@/components/data-table"
import type { SalesOrderStatus } from "../types/sales.types"

export const SO_STATUS_OPTIONS: FacetedFilterOption[] = [
  { label: "Draft", value: "draft" },
  { label: "Confirmed", value: "confirmed" },
  { label: "Fulfilled", value: "fulfilled" },
  { label: "Cancelled", value: "cancelled" },
]

export const SO_STATUS_COLOR_MAP: Record<
  SalesOrderStatus,
  { bg: string; text: string }
> = {
  draft: {
    bg: "bg-gray-100 dark:bg-gray-800/30",
    text: "text-gray-800 dark:text-gray-300",
  },
  confirmed: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-800 dark:text-blue-300",
  },
  fulfilled: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-800 dark:text-green-300",
  },
  cancelled: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-800 dark:text-red-300",
  },
}
