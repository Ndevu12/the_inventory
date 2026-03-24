import type { ReportPeriod, ValuationMethod } from "../types/reports.types"

/** Maps `stock-valuation` → `stockValuation` for `Reports.cards.*` message keys. */
export function reportCardKeyFromId(id: string): string {
  return id.replace(/-([a-z])/g, (_, c: string) => c.toUpperCase())
}

export interface ReportDefinition {
  id: string
  icon: string
  path: string
}

export const REPORT_DEFINITIONS: ReportDefinition[] = [
  {
    id: "stock-valuation",
    icon: "DollarSign",
    path: "/reports/stock-valuation",
  },
  {
    id: "movement-history",
    icon: "ArrowLeftRight",
    path: "/reports/movement-history",
  },
  {
    id: "low-stock",
    icon: "AlertTriangle",
    path: "/reports/low-stock",
  },
  {
    id: "overstock",
    icon: "TrendingUp",
    path: "/reports/overstock",
  },
  {
    id: "purchase-summary",
    icon: "ShoppingCart",
    path: "/reports/purchase-summary",
  },
  {
    id: "sales-summary",
    icon: "Receipt",
    path: "/reports/sales-summary",
  },
  {
    id: "availability",
    icon: "PackageCheck",
    path: "/reports/availability",
  },
  {
    id: "product-expiry",
    icon: "Clock",
    path: "/reports/product-expiry",
  },
  {
    id: "variances",
    icon: "Scale",
    path: "/reports/variances",
  },
  {
    id: "traceability",
    icon: "Search",
    path: "/reports/traceability",
  },
]

export const REPORT_PERIOD_VALUES: ReportPeriod[] = ["daily", "weekly", "monthly"]

export const VALUATION_METHOD_VALUES: ValuationMethod[] = [
  "weighted_average",
  "latest_cost",
]

export const MOVEMENT_TYPE_VALUES = [
  "receipt",
  "issue",
  "transfer",
  "adjustment",
  "return",
] as const

export const VARIANCE_TYPE_VALUES = [
  "shortage",
  "surplus",
  "match",
] as const
