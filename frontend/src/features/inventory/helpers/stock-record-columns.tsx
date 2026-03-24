"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header"
import { LowStockBadge } from "../components/stock-records/low-stock-badge"
import type { StockRecord } from "../types/inventory.types"

type StockRecordT = (key: string) => string

export function createStockRecordColumns(
  t: StockRecordT,
): ColumnDef<StockRecord>[] {
  return [
    {
      accessorKey: "product_sku",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("stockRecords.columns.sku")} />
      ),
      cell: ({ row }) => (
        <span className="font-mono text-sm">{row.getValue("product_sku")}</span>
      ),
    },
    {
      accessorKey: "product_name",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.product")}
        />
      ),
    },
    {
      accessorKey: "location_name",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.location")}
        />
      ),
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.quantity")}
        />
      ),
      cell: ({ row }) => (
        <span className="tabular-nums">{row.getValue<number>("quantity")}</span>
      ),
    },
    {
      accessorKey: "reserved_quantity",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.reserved")}
        />
      ),
      cell: ({ row }) => (
        <span className="tabular-nums">
          {row.getValue<number>("reserved_quantity")}
        </span>
      ),
    },
    {
      accessorKey: "available_quantity",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.available")}
        />
      ),
      cell: ({ row }) => {
        const available = row.getValue<number>("available_quantity")
        const isLow = row.original.is_low_stock
        return (
          <span
            className={`tabular-nums ${isLow ? "font-semibold text-destructive" : ""}`}
          >
            {available}
          </span>
        )
      },
    },
    {
      accessorKey: "is_low_stock",
      header: ({ column }) => (
        <DataTableColumnHeader
          column={column}
          title={t("stockRecords.columns.status")}
        />
      ),
      cell: ({ row }) => (
        <LowStockBadge isLowStock={row.original.is_low_stock} />
      ),
      filterFn: (row, _id, value: string[]) => {
        if (!value || value.length === 0) return true
        const isLow = row.original.is_low_stock
        return value.includes(isLow ? "low" : "ok")
      },
    },
  ]
}
