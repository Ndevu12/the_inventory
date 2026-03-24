"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import type { ColumnDef, PaginationState } from "@tanstack/react-table";
import { CheckCircleIcon, XCircleIcon } from "lucide-react";
import { DataTable } from "@/components/data-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import {
  DataTableRowActions,
  type RowAction,
} from "@/components/data-table/data-table-row-actions";
import type { StockReservation } from "../types/reservation.types";
import { ReservationStatusBadge } from "./reservation-status-badge";

interface ReservationTableProps {
  data: StockReservation[];
  pageCount: number;
  pagination: PaginationState;
  onPaginationChange: (state: PaginationState) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  onFulfill: (reservation: StockReservation) => void;
  onCancel: (reservation: StockReservation) => void;
  filterContent?: React.ReactNode;
  isLoading?: boolean;
}

export function ReservationTable({
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  onFulfill,
  onCancel,
  filterContent,
  isLoading = false,
}: ReservationTableProps) {
  const t = useTranslations("Reservations.table");
  const tDash = useTranslations("Inventory.shared");

  const columns = useMemo<ColumnDef<StockReservation, unknown>[]>(
    () => [
      {
        accessorKey: "product_name",
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title={t("product")} />
        ),
        cell: ({ row }) => (
          <div>
            <span className="font-medium">{row.original.product_name}</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {row.original.product_sku}
            </span>
          </div>
        ),
        enableSorting: false,
      },
      {
        accessorKey: "location_name",
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title={t("location")} />
        ),
        enableSorting: false,
      },
      {
        accessorKey: "quantity",
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title={t("qty")} />
        ),
      },
      {
        accessorKey: "status",
        header: t("status"),
        cell: ({ row }) => (
          <ReservationStatusBadge status={row.original.status} />
        ),
        filterFn: (row, _id, filterValue: string[]) => {
          if (!filterValue || filterValue.length === 0) return true;
          return filterValue.includes(row.original.status);
        },
      },
      {
        accessorKey: "sales_order_number",
        header: t("salesOrder"),
        cell: ({ row }) =>
          row.original.sales_order_number ?? tDash("emDash"),
        enableSorting: false,
      },
      {
        accessorKey: "reserved_by_username",
        header: t("reservedBy"),
        cell: ({ row }) =>
          row.original.reserved_by_username ?? tDash("emDash"),
        enableSorting: false,
      },
      {
        accessorKey: "expires_at",
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title={t("expires")} />
        ),
        cell: ({ row }) => {
          const expiresAt = row.original.expires_at;
          if (!expiresAt) return tDash("emDash");
          return new Date(expiresAt).toLocaleDateString();
        },
      },
      {
        accessorKey: "created_at",
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title={t("created")} />
        ),
        cell: ({ row }) =>
          new Date(row.original.created_at).toLocaleDateString(),
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const reservation = row.original;
          const canAct =
            reservation.status === "pending" ||
            reservation.status === "confirmed";

          if (!canAct) return null;

          const actions: RowAction<StockReservation>[] = [];

          actions.push({
            label: t("fulfill"),
            icon: <CheckCircleIcon className="size-4" />,
            onClick: () => onFulfill(reservation),
          });

          actions.push({
            label: t("cancelReservation"),
            icon: <XCircleIcon className="size-4" />,
            onClick: () => onCancel(reservation),
            variant: "destructive",
            separator: true,
          });

          return <DataTableRowActions row={row} actions={actions} />;
        },
      },
    ],
    [onFulfill, onCancel, t, tDash],
  );

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder={t("searchPlaceholder")}
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage={t("empty")}
    />
  );
}
