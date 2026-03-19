"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { LowStockBadge } from "../components/stock-records/low-stock-badge";
import type { StockRecord } from "../types/inventory.types";

export const stockRecordColumns: ColumnDef<StockRecord>[] = [
  {
    accessorKey: "product_sku",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="SKU" />
    ),
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.getValue("product_sku")}</span>
    ),
  },
  {
    accessorKey: "product_name",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Product" />
    ),
  },
  {
    accessorKey: "location_name",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Location" />
    ),
  },
  {
    accessorKey: "quantity",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Quantity" />
    ),
    cell: ({ row }) => (
      <span className="tabular-nums">{row.getValue<number>("quantity")}</span>
    ),
  },
  {
    accessorKey: "reserved_quantity",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Reserved" />
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
      <DataTableColumnHeader column={column} title="Available" />
    ),
    cell: ({ row }) => {
      const available = row.getValue<number>("available_quantity");
      const isLow = row.original.is_low_stock;
      return (
        <span
          className={`tabular-nums ${isLow ? "font-semibold text-destructive" : ""}`}
        >
          {available}
        </span>
      );
    },
  },
  {
    accessorKey: "is_low_stock",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Status" />
    ),
    cell: ({ row }) => <LowStockBadge isLowStock={row.original.is_low_stock} />,
    filterFn: (row, _id, value: string[]) => {
      if (!value || value.length === 0) return true;
      const isLow = row.original.is_low_stock;
      return value.includes(isLow ? "low" : "ok");
    },
  },
];
