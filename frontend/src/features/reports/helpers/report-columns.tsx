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

export function getStockValuationColumns(): ColumnDef<StockValuationItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => row.getValue("category") || "—",
    },
    {
      accessorKey: "total_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Quantity" />,
      cell: ({ row }) => formatNumber(row.getValue("total_quantity")),
    },
    {
      accessorKey: "unit_cost",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Unit Cost" />,
      cell: ({ row }) => formatCurrency(row.getValue("unit_cost")),
    },
    {
      accessorKey: "total_value",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Total Value" />,
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

export function getMovementHistoryColumns(): ColumnDef<MovementHistoryItem>[] {
  return [
    {
      accessorKey: "product_sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("product_sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "movement_type",
      header: "Type",
      cell: ({ row }) => {
        const type = row.getValue<string>("movement_type")
        return (
          <Badge variant={MOVEMENT_TYPE_VARIANT[type] ?? "secondary"}>
            {type}
          </Badge>
        )
      },
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Qty" />,
      cell: ({ row }) => formatNumber(row.getValue("quantity")),
    },
    {
      accessorKey: "unit_cost",
      header: "Unit Cost",
      cell: ({ row }) => {
        const val = row.getValue<string | null>("unit_cost")
        return val ? formatCurrency(Number(val)) : "—"
      },
    },
    {
      accessorKey: "from_location",
      header: "From",
      cell: ({ row }) => row.getValue("from_location") || "—",
    },
    {
      accessorKey: "to_location",
      header: "To",
      cell: ({ row }) => row.getValue("to_location") || "—",
    },
    {
      accessorKey: "reference",
      header: "Reference",
      cell: ({ row }) => row.getValue("reference") || "—",
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Date" />,
      cell: ({ row }) => formatDate(row.getValue("created_at"), { includeTime: true }),
    },
  ]
}

export function getLowStockColumns(): ColumnDef<LowStockItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => row.getValue("category") || "—",
    },
    {
      accessorKey: "reorder_point",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Reorder Point" />,
      cell: ({ row }) => formatNumber(row.getValue("reorder_point")),
    },
    {
      accessorKey: "total_stock",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Current Stock" />,
      cell: ({ row }) => formatNumber(row.getValue("total_stock")),
    },
    {
      accessorKey: "deficit",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Deficit" />,
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

export function getOverstockColumns(): ColumnDef<OverstockItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => row.getValue("category") || "—",
    },
    {
      accessorKey: "reorder_point",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Reorder Point" />,
      cell: ({ row }) => formatNumber(row.getValue("reorder_point")),
    },
    {
      accessorKey: "total_stock",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Current Stock" />,
      cell: ({ row }) => formatNumber(row.getValue("total_stock")),
    },
    {
      accessorKey: "threshold",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Threshold" />,
      cell: ({ row }) => formatNumber(row.getValue("threshold")),
    },
    {
      accessorKey: "excess",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Excess" />,
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

export function getPeriodSummaryColumns(totalLabel: string): ColumnDef<PeriodSummaryItem>[] {
  return [
    {
      accessorKey: "period",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Period" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("period")}</span>,
    },
    {
      accessorKey: "order_count",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Orders" />,
      cell: ({ row }) => formatNumber(row.getValue("order_count")),
    },
    {
      accessorKey: "total",
      header: ({ column }) => <DataTableColumnHeader column={column} title={totalLabel} />,
      cell: ({ row }) => formatCurrency(Number(row.getValue("total"))),
    },
  ]
}

export function getAvailabilityColumns(): ColumnDef<AvailabilityItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => row.getValue("category") || "—",
    },
    {
      accessorKey: "total_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Total Qty" />,
      cell: ({ row }) => formatNumber(row.getValue("total_quantity")),
    },
    {
      accessorKey: "reserved_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Reserved" />,
      cell: ({ row }) => formatNumber(row.getValue("reserved_quantity")),
    },
    {
      accessorKey: "available_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Available" />,
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
      header: "Unit Cost",
      cell: ({ row }) => formatCurrency(Number(row.getValue("unit_cost"))),
    },
    {
      accessorKey: "reserved_value",
      header: "Reserved Value",
      cell: ({ row }) => formatCurrency(Number(row.getValue("reserved_value"))),
    },
  ]
}

export function getProductExpiryColumns(): ColumnDef<ProductExpiryItem>[] {
  return [
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue<string>("status")
        return (
          <Badge variant={status === "expired" ? "destructive" : "secondary"}>
            {status === "expired" ? "Expired" : "Expiring"}
          </Badge>
        )
      },
    },
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "lot_number",
      header: "Lot Number",
    },
    {
      accessorKey: "expiry_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Expiry Date" />,
      cell: ({ row }) => formatDate(row.getValue("expiry_date")),
    },
    {
      accessorKey: "days_to_expiry",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Days Left" />,
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
      header: ({ column }) => <DataTableColumnHeader column={column} title="Qty Remaining" />,
      cell: ({ row }) => formatNumber(row.getValue("quantity_remaining")),
    },
    {
      accessorKey: "supplier",
      header: "Supplier",
      cell: ({ row }) => row.getValue("supplier") || "—",
    },
  ]
}

const VARIANCE_TYPE_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  shortage: "destructive",
  surplus: "secondary",
  match: "default",
}

export function getVarianceColumns(): ColumnDef<VarianceItem>[] {
  return [
    {
      accessorKey: "cycle_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Cycle" />,
    },
    {
      accessorKey: "product_sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("product_sku")}</span>,
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Product" />,
    },
    {
      accessorKey: "location",
      header: "Location",
    },
    {
      accessorKey: "variance_type",
      header: "Type",
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
      header: ({ column }) => <DataTableColumnHeader column={column} title="System Qty" />,
      cell: ({ row }) => formatNumber(row.getValue("system_quantity")),
    },
    {
      accessorKey: "physical_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Physical Qty" />,
      cell: ({ row }) => formatNumber(row.getValue("physical_quantity")),
    },
    {
      accessorKey: "variance_quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Variance" />,
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
      header: "Resolution",
      cell: ({ row }) => row.getValue("resolution") || "—",
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Date" />,
      cell: ({ row }) => formatDate(row.getValue("created_at")),
    },
  ]
}

export function getCycleHistoryColumns(): ColumnDef<CycleHistoryItem>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("name")}</span>,
    },
    {
      accessorKey: "status_display",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant="secondary">{row.getValue("status_display")}</Badge>
      ),
    },
    {
      accessorKey: "location",
      header: "Location",
      cell: ({ row }) => row.getValue("location") || "All",
    },
    {
      accessorKey: "scheduled_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Scheduled" />,
      cell: ({ row }) => formatDate(row.getValue("scheduled_date")),
    },
    {
      accessorKey: "total_lines",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Lines" />,
      cell: ({ row }) => formatNumber(row.getValue("total_lines")),
    },
    {
      accessorKey: "total_variances",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Variances" />,
      cell: ({ row }) => formatNumber(row.getValue("total_variances")),
    },
    {
      accessorKey: "shortages",
      header: "Shortages",
      cell: ({ row }) => formatNumber(row.getValue("shortages")),
    },
    {
      accessorKey: "surpluses",
      header: "Surpluses",
      cell: ({ row }) => formatNumber(row.getValue("surpluses")),
    },
    {
      accessorKey: "net_variance",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Net Variance" />,
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

export function getTraceabilityColumns(): ColumnDef<TraceabilityChainEntry>[] {
  return [
    {
      accessorKey: "action",
      header: "Action",
      cell: ({ row }) => (
        <Badge variant="secondary">{row.getValue("action")}</Badge>
      ),
    },
    {
      accessorKey: "date",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Date" />,
      cell: ({ row }) => formatDate(row.getValue("date"), { includeTime: true }),
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Quantity" />,
      cell: ({ row }) => formatNumber(row.getValue("quantity")),
    },
    {
      id: "from_location",
      header: "From / Location",
      cell: ({ row }) => row.original.location || row.original.from || "—",
    },
    {
      id: "to_location",
      header: "To",
      cell: ({ row }) => row.original.to || "—",
    },
    {
      id: "sales_order",
      header: "Sales Order",
      cell: ({ row }) => row.original.sales_order || "—",
    },
  ]
}
