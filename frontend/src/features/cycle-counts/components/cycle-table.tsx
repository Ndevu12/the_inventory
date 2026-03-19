"use client";

import { useMemo } from "react";
import type { PaginationState } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import type { InventoryCycle } from "../types/cycle-count.types";
import { getCycleColumns } from "./cycle-columns";

interface CycleTableProps {
  data: InventoryCycle[];
  pageCount: number;
  pagination: PaginationState;
  onPaginationChange: (state: PaginationState) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  filterContent?: React.ReactNode;
  isLoading?: boolean;
}

export function CycleTable({
  data,
  pageCount,
  pagination,
  onPaginationChange,
  searchValue,
  onSearchChange,
  filterContent,
  isLoading = false,
}: CycleTableProps) {
  const columns = useMemo(() => getCycleColumns(), []);

  return (
    <DataTable
      columns={columns}
      data={data}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={onPaginationChange}
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      searchPlaceholder="Search cycle counts..."
      filterContent={filterContent}
      isLoading={isLoading}
      emptyMessage="No cycle counts found."
    />
  );
}
