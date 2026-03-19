"use client";

import Link from "next/link";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import type { InventoryCycle } from "../types/cycle-count.types";
import { CycleStatusBadge } from "./cycle-status-badge";

export function getCycleColumns(): ColumnDef<InventoryCycle, unknown>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Name" />
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
      header: "Location",
      cell: ({ row }) => row.original.location_name ?? "All Locations",
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <CycleStatusBadge status={row.original.status} />,
      filterFn: (row, _id, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        return filterValue.includes(row.original.status);
      },
    },
    {
      accessorKey: "scheduled_date",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Scheduled" />
      ),
      cell: ({ row }) =>
        new Date(row.original.scheduled_date).toLocaleDateString(),
    },
    {
      id: "progress",
      header: "Progress",
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
      header: "Started By",
      cell: ({ row }) => row.original.started_by_username ?? "—",
      enableSorting: false,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Created" />
      ),
      cell: ({ row }) =>
        new Date(row.original.created_at).toLocaleDateString(),
    },
  ];
}
