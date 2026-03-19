"use client";

import type { ColumnDef } from "@tanstack/react-table";
import type { StockLot } from "../types/lot.types";

export function getLotColumns(): ColumnDef<StockLot>[] {
  return [
    {
      accessorKey: "lot_number",
      header: "Lot Number",
      enableSorting: true,
    },
    {
      accessorKey: "product_sku",
      header: "Product SKU",
      enableSorting: false,
    },
    {
      accessorKey: "serial_number",
      header: "Serial Number",
      enableSorting: false,
      cell: ({ row }) => row.original.serial_number ?? "—",
    },
    {
      accessorKey: "quantity_received",
      header: "Qty Received",
      enableSorting: false,
      cell: ({ row }) => row.original.quantity_received.toLocaleString(),
    },
    {
      accessorKey: "quantity_remaining",
      header: "Qty Remaining",
      enableSorting: true,
      cell: ({ row }) => row.original.quantity_remaining.toLocaleString(),
    },
    {
      accessorKey: "received_date",
      header: "Received",
      enableSorting: true,
      cell: ({ row }) =>
        new Date(row.original.received_date).toLocaleDateString(),
    },
    {
      accessorKey: "expiry_date",
      header: "Expiry Date",
      enableSorting: true,
      cell: ({ row }) =>
        row.original.expiry_date
          ? new Date(row.original.expiry_date).toLocaleDateString()
          : "—",
    },
    {
      id: "expiry_status",
      header: "Expiry Status",
      enableSorting: false,
    },
    {
      accessorKey: "is_active",
      header: "Status",
      enableSorting: false,
    },
  ];
}
