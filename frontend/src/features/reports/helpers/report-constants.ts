import type { ReportPeriod, ValuationMethod } from "../types/reports.types"

export interface ReportDefinition {
  id: string
  name: string
  description: string
  icon: string
  path: string
}

export const REPORT_DEFINITIONS: ReportDefinition[] = [
  {
    id: "stock-valuation",
    name: "Stock Valuation",
    description: "View total inventory value using weighted average or latest cost methods",
    icon: "DollarSign",
    path: "/reports/stock-valuation",
  },
  {
    id: "movement-history",
    name: "Movement History",
    description: "Browse all stock movements with date range and type filters",
    icon: "ArrowLeftRight",
    path: "/reports/movement-history",
  },
  {
    id: "low-stock",
    name: "Low Stock",
    description: "Products at or below their reorder point",
    icon: "AlertTriangle",
    path: "/reports/low-stock",
  },
  {
    id: "overstock",
    name: "Overstock",
    description: "Products exceeding their reorder point threshold",
    icon: "TrendingUp",
    path: "/reports/overstock",
  },
  {
    id: "purchase-summary",
    name: "Purchase Summary",
    description: "Purchase order totals grouped by period",
    icon: "ShoppingCart",
    path: "/reports/purchase-summary",
  },
  {
    id: "sales-summary",
    name: "Sales Summary",
    description: "Sales order totals grouped by period",
    icon: "Receipt",
    path: "/reports/sales-summary",
  },
  {
    id: "availability",
    name: "Availability",
    description: "Per-product stock, reserved, and available quantities",
    icon: "PackageCheck",
    path: "/reports/availability",
  },
  {
    id: "product-expiry",
    name: "Product Expiry",
    description: "Lots expiring soon or already expired",
    icon: "Clock",
    path: "/reports/product-expiry",
  },
  {
    id: "variances",
    name: "Variances",
    description: "Inventory variance report from cycle counts",
    icon: "Scale",
    path: "/reports/variances",
  },
  {
    id: "traceability",
    name: "Traceability",
    description: "Full movement chain for a specific product and lot",
    icon: "Search",
    path: "/reports/traceability",
  },
]

export const PERIOD_OPTIONS: { value: ReportPeriod; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
]

export const VALUATION_METHOD_OPTIONS: { value: ValuationMethod; label: string }[] = [
  { value: "weighted_average", label: "Weighted Average" },
  { value: "latest_cost", label: "Latest Cost" },
]

export const MOVEMENT_TYPE_OPTIONS = [
  { value: "receipt", label: "Receipt" },
  { value: "issue", label: "Issue" },
  { value: "transfer", label: "Transfer" },
  { value: "adjustment", label: "Adjustment" },
  { value: "return", label: "Return" },
]

export const VARIANCE_TYPE_OPTIONS = [
  { value: "shortage", label: "Shortage" },
  { value: "surplus", label: "Surplus" },
  { value: "match", label: "Match" },
]
