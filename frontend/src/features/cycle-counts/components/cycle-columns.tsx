"use client";

import { Link } from "@/i18n/navigation";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import type { InventoryCycle } from "../types/cycle-count.types";
import { CycleStatusBadge } from "./cycle-status-badge";

export function getCycleColumns(
  t: (key: string) => string,
): ColumnDef<InventoryCycle, unknown>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("name")} />
      ),
      cell: ({ row }) => (
        <Link
          href={`/cycle-counts/${row.original.id}`}
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          {row.original.name}
        </Link>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "location_name",
      header: t("location"),
      cell: ({ row }) => row.original.location_name ?? t("allLocations"),
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: t("status"),
      cell: ({ row }) => <CycleStatusBadge status={row.original.status} />,
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        return filterValue.includes(row.original.status);
      },
    },
    {
      accessorKey: "scheduled_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("scheduled")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.scheduled_date).toLocaleDateString(),
    },
    {
      id: "progress",
      header: t("progress"),
      cell: ({ row }) => {
        const { counted_lines, total_lines } = row.original;
        return (
          <span className="text-sm text-muted-foreground">
            {counted_lines} / {total_lines}
          </span>
        );
      },
      enableSorting: false,
    },
    {
      accessorKey: "started_by_username",
      header: t("startedBy"),
      cell: ({ row }) =>
        row.original.started_by_username ?? "\u2014",
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title={t("created")} />
      ),
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(),
    },
  ];
}
