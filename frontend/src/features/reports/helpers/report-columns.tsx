"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { DataTableColumnHeader } from "@/components/data-table"
import { formatCurrency, formatDate, formatNumber } from "@/lib/utils/format"
import type {
  StockValuationItem,
  MovementHistoryItem,
  LowStockItem,
  OverstockItem,
  PeriodSummaryItem,
  AvailabilityItem,
  ProductExpiryItem,
  VarianceItem,
  CycleHistoryItem,
  TraceabilityChainEntry,
} from "../types/reports.types"

/** Labels from `Reports.columns` (and related) via `useTranslations`. */
export type ReportColumnT = (key: string) => string

export function getStockValuationColumns(t: ReportColumnT): ColumnDef<StockValuationItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "category",
      header: t("category"),
      cell: ({ row }) => row.getValue("category") || empty,
    },
    {
      accessorKey: "total_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("quantity")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_quantity")),
    },
    {
      accessorKey: "unit_cost",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("unitCost")} />,
      cell: ({ row }) => formatCurrency(row.getValue("unit_cost")),
    },
    {
      accessorKey: "total_value",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("totalValue")} />,
      cell: ({ row }) => formatCurrency(row.getValue("total_value")),
    },
  ]
}

const MOVEMENT_TYPE_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  receipt: "default",
  issue: "destructive",
  transfer: "secondary",
  adjustment: "outline",
  return: "secondary",
}

export function getMovementHistoryColumns(
  t: ReportColumnT,
  movementLabel: (type: string) => string,
): ColumnDef<MovementHistoryItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "product_sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("product_sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "movement_type",
      header: t("type"),
      cell: ({ row }) => {
        const type = row.getValue<string>("movement_type")
        return (
          <Badge variant={MOVEMENT_TYPE_VARIANT[type] ?? "secondary"}>
            {movementLabel(type)}
          </Badge>
        )
      },
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("qty")} />,
      cell: ({ row }) => formatNumber(row.getValue("quantity")),
    },
    {
      accessorKey: "unit_cost",
      header: t("unitCost"),
      cell: ({ row }) => {
        const val = row.getValue<string | null>("unit_cost")
        return val ? formatCurrency(Number(val)) : empty
      },
    },
    {
      accessorKey: "from_location",
      header: t("from"),
      cell: ({ row }) => row.getValue("from_location") || empty,
    },
    {
      accessorKey: "to_location",
      header: t("to"),
      cell: ({ row }) => row.getValue("to_location") || empty,
    },
    {
      accessorKey: "reference",
      header: t("reference"),
      cell: ({ row }) => row.getValue("reference") || empty,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("date")} />,
      cell: ({ row }) => formatDate(row.getValue("created_at"), { includeTime: true }),
    },
  ]
}

export function getLowStockColumns(t: ReportColumnT): ColumnDef<LowStockItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "category",
      header: t("category"),
      cell: ({ row }) => row.getValue("category") || empty,
    },
    {
      accessorKey: "reorder_point",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("reorderPoint")} />,
      cell: ({ row }) => formatNumber(row.getValue("reorder_point")),
    },
    {
      accessorKey: "total_stock",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("currentStock")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_stock")),
    },
    {
      accessorKey: "deficit",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("deficit")} />,
      cell: ({ row }) => {
        const deficit = row.getValue<number>("deficit")
        return (
          <span className="font-medium text-destructive">
            {formatNumber(deficit)}
          </span>
        )
      },
    },
  ]
}

export function getOverstockColumns(t: ReportColumnT): ColumnDef<OverstockItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "category",
      header: t("category"),
      cell: ({ row }) => row.getValue("category") || empty,
    },
    {
      accessorKey: "reorder_point",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("reorderPoint")} />,
      cell: ({ row }) => formatNumber(row.getValue("reorder_point")),
    },
    {
      accessorKey: "total_stock",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("currentStock")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_stock")),
    },
    {
      accessorKey: "threshold",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("threshold")} />,
      cell: ({ row }) => formatNumber(row.getValue("threshold")),
    },
    {
      accessorKey: "excess",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("excess")} />,
      cell: ({ row }) => {
        const excess = row.getValue<number>("excess")
        return (
          <span className="font-medium text-amber-600 dark:text-amber-400">
            +{formatNumber(excess)}
          </span>
        )
      },
    },
  ]
}

export function getPeriodSummaryColumns(
  t: ReportColumnT,
  totalColumnKey: "totalCost" | "totalRevenue",
): ColumnDef<PeriodSummaryItem>[] {
  return [
    {
      accessorKey: "period",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("period")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("period")}</span>,
    },
    {
      accessorKey: "order_count",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("orders")} />,
      cell: ({ row }) => formatNumber(row.getValue("order_count")),
    },
    {
      accessorKey: "total",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t(totalColumnKey)} />
      ),
      cell: ({ row }) => formatCurrency(Number(row.getValue("total"))),
    },
  ]
}

export function getAvailabilityColumns(t: ReportColumnT): ColumnDef<AvailabilityItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "category",
      header: t("category"),
      cell: ({ row }) => row.getValue("category") || empty,
    },
    {
      accessorKey: "total_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("totalQty")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_quantity")),
    },
    {
      accessorKey: "reserved_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("reserved")} />,
      cell: ({ row }) => formatNumber(row.getValue("reserved_quantity")),
    },
    {
      accessorKey: "available_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("available")} />,
      cell: ({ row }) => {
        const available = row.getValue<number>("available_quantity")
        return (
          <span className={available <= 0 ? "text-destructive font-medium" : ""}>
            {formatNumber(available)}
          </span>
        )
      },
    },
    {
      accessorKey: "unit_cost",
      header: t("unitCost"),
      cell: ({ row }) => formatCurrency(Number(row.getValue("unit_cost"))),
    },
    {
      accessorKey: "reserved_value",
      header: t("reservedValue"),
      cell: ({ row }) => formatCurrency(Number(row.getValue("reserved_value"))),
    },
  ]
}

export function getProductExpiryColumns(
  t: ReportColumnT,
  expiryBadge: (key: "expired" | "expiring") => string,
): ColumnDef<ProductExpiryItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "status",
      header: t("status"),
      cell: ({ row }) => {
        const status = row.getValue<string>("status")
        return (
          <Badge variant={status === "expired" ? "destructive" : "secondary"}>
            {status === "expired" ? expiryBadge("expired") : expiryBadge("expiring")}
          </Badge>
        )
      },
    },
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "lot_number",
      header: t("lotNumber"),
    },
    {
      accessorKey: "expiry_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("expiryDate")} />,
      cell: ({ row }) => formatDate(row.getValue("expiry_date")),
    },
    {
      accessorKey: "days_to_expiry",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("daysLeft")} />,
      cell: ({ row }) => {
        const days = row.getValue<number>("days_to_expiry")
        return (
          <span className={days <= 0 ? "text-destructive font-medium" : days <= 7 ? "text-amber-600 dark:text-amber-400 font-medium" : ""}>
            {days}
          </span>
        )
      },
    },
    {
      accessorKey: "quantity_remaining",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("qtyRemaining")} />,
      cell: ({ row }) => formatNumber(row.getValue("quantity_remaining")),
    },
    {
      accessorKey: "supplier",
      header: t("supplier"),
      cell: ({ row }) => row.getValue("supplier") || empty,
    },
  ]
}

const VARIANCE_TYPE_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  shortage: "destructive",
  surplus: "secondary",
  match: "default",
}

export function getVarianceColumns(t: ReportColumnT): ColumnDef<VarianceItem>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "cycle_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("cycle")} />,
    },
    {
      accessorKey: "product_sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("sku")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("product_sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("product")} />,
    },
    {
      accessorKey: "location",
      header: t("location"),
    },
    {
      accessorKey: "variance_type",
      header: t("type"),
      cell: ({ row }) => {
        const type = row.getValue<string>("variance_type")
        return (
          <Badge variant={VARIANCE_TYPE_VARIANT[type] ?? "secondary"}>
            {row.original.variance_type_display}
          </Badge>
        )
      },
    },
    {
      accessorKey: "system_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("systemQty")} />,
      cell: ({ row }) => formatNumber(row.getValue("system_quantity")),
    },
    {
      accessorKey: "physical_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("physicalQty")} />,
      cell: ({ row }) => formatNumber(row.getValue("physical_quantity")),
    },
    {
      accessorKey: "variance_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("variance")} />,
      cell: ({ row }) => {
        const v = row.getValue<number>("variance_quantity")
        return (
          <span className={v < 0 ? "text-destructive font-medium" : v > 0 ? "text-amber-600 dark:text-amber-400 font-medium" : ""}>
            {v > 0 ? "+" : ""}{formatNumber(v)}
          </span>
        )
      },
    },
    {
      accessorKey: "resolution",
      header: t("resolution"),
      cell: ({ row }) => row.getValue("resolution") || empty,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("date")} />,
      cell: ({ row }) => formatDate(row.getValue("created_at")),
    },
  ]
}

/** Reserved for cycle-history report UI; pass `Reports.columns` via `t`. */
export function getCycleHistoryColumns(t: ReportColumnT): ColumnDef<CycleHistoryItem>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("name")} />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("name")}</span>,
    },
    {
      accessorKey: "status_display",
      header: t("status"),
      cell: ({ row }) => (
        <Badge variant="secondary">{row.getValue("status_display")}</Badge>
      ),
    },
    {
      accessorKey: "location",
      header: t("location"),
      cell: ({ row }) => row.getValue("location") || t("allLocations"),
    },
    {
      accessorKey: "scheduled_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("scheduled")} />,
      cell: ({ row }) => formatDate(row.getValue("scheduled_date")),
    },
    {
      accessorKey: "total_lines",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("lines")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_lines")),
    },
    {
      accessorKey: "total_variances",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("variances")} />,
      cell: ({ row }) => formatNumber(row.getValue("total_variances")),
    },
    {
      accessorKey: "shortages",
      header: t("shortages"),
      cell: ({ row }) => formatNumber(row.getValue("shortages")),
    },
    {
      accessorKey: "surpluses",
      header: t("surpluses"),
      cell: ({ row }) => formatNumber(row.getValue("surpluses")),
    },
    {
      accessorKey: "net_variance",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("netVariance")} />,
      cell: ({ row }) => {
        const v = row.getValue<number>("net_variance")
        return (
          <span className={v < 0 ? "text-destructive font-medium" : v > 0 ? "text-amber-600 dark:text-amber-400 font-medium" : ""}>
            {v > 0 ? "+" : ""}{formatNumber(v)}
          </span>
        )
      },
    },
  ]
}

export function getTraceabilityColumns(t: ReportColumnT): ColumnDef<TraceabilityChainEntry>[] {
  const empty = t("cellEmpty")
  return [
    {
      accessorKey: "action",
      header: t("action"),
      cell: ({ row }) => (
        <Badge variant="secondary">{row.getValue("action")}</Badge>
      ),
    },
    {
      accessorKey: "date",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("date")} />,
      cell: ({ row }) => formatDate(row.getValue("date"), { includeTime: true }),
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("quantity")} />,
      cell: ({ row }) => formatNumber(row.getValue("quantity")),
    },
    {
      id: "from_location",
      header: t("fromToLocation"),
      cell: ({ row }) => row.original.location || row.original.from || empty,
    },
    {
      id: "to_location",
      header: t("to"),
      cell: ({ row }) => row.original.to || empty,
    },
    {
      id: "sales_order",
      header: t("salesOrder"),
      cell: ({ row }) => row.original.sales_order || empty,
    },
  ]
}
