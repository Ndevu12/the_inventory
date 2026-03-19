import type { ColumnDef } from "@tanstack/react-table";
import type { StockReservation } from "../types/reservation.types";

export function getReservationColumns(opts: {
  onFulfill: (reservation: StockReservation) => void;
  onCancel: (reservation: StockReservation) => void;
}): ColumnDef<StockReservation, unknown>[] {
  return [
    {
      accessorKey: "product_name",
      header: "Product",
      cell: ({ row }) => {
        const sku = row.original.product_sku;
        const name = row.original.product_name;
        return `${sku} — ${name}`;
      },
    },
    {
      accessorKey: "location_name",
      header: "Location",
    },
    {
      accessorKey: "quantity",
      header: "Qty",
    },
    {
      accessorKey: "status",
      header: "Status",
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        return filterValue.includes(row.original.status);
      },
    },
    {
      accessorKey: "sales_order_number",
      header: "Sales Order",
      cell: ({ row }) => row.original.sales_order_number ?? "—",
    },
    {
      accessorKey: "reserved_by_username",
      header: "Reserved By",
      cell: ({ row }) => row.original.reserved_by_username ?? "—",
    },
    {
      accessorKey: "expires_at",
      header: "Expires",
      cell: ({ row }) => {
        const expiresAt = row.original.expires_at;
        if (!expiresAt) return "—";
        return new Date(expiresAt).toLocaleDateString();
      },
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(),
    },
    {
      id: "actions",
      header: "",
      meta: { onFulfill: opts.onFulfill, onCancel: opts.onCancel },
    },
  ];
}
