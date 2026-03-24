import type { ColumnDef } from "@tanstack/react-table"
import type { StockLot } from "../types/lot.types"

type LotColumnT = (key: string) => string

export function createLotColumns(t: LotColumnT): ColumnDef<StockLot>[] {
  return [
    {
      accessorKey: "lot_number",
      header: t("lots.columns.lotNumber"),
      enableSorting: true,
    },
    {
      accessorKey: "product_sku",
      header: t("lots.columns.productSku"),
      enableSorting: false,
    },
    {
      accessorKey: "serial_number",
      header: t("lots.columns.serialNumber"),
      enableSorting: false,
      cell: ({ row }) => row.original.serial_number ?? t("shared.emDash"),
    },
    {
      accessorKey: "quantity_received",
      header: t("lots.columns.qtyReceived"),
      enableSorting: false,
      cell: ({ row }) => row.original.quantity_received.toLocaleString(),
    },
    {
      accessorKey: "quantity_remaining",
      header: t("lots.columns.qtyRemaining"),
      enableSorting: true,
      cell: ({ row }) => row.original.quantity_remaining.toLocaleString(),
    },
    {
      accessorKey: "received_date",
      header: t("lots.columns.received"),
      enableSorting: true,
      cell: ({ row }) =>
        new Date(row.original.received_date).toLocaleDateString(),
    },
    {
      accessorKey: "expiry_date",
      header: t("lots.columns.expiryDate"),
      enableSorting: true,
      cell: ({ row }) =>
        row.original.expiry_date
          ? new Date(row.original.expiry_date).toLocaleDateString()
          : t("shared.emDash"),
    },
    {
      id: "expiry_status",
      header: t("lots.columns.expiryStatus"),
      enableSorting: false,
    },
    {
      accessorKey: "is_active",
      header: t("lots.columns.status"),
      enableSorting: false,
    },
  ]
}
