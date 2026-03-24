"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("CycleCounts.list");
  const tTable = useTranslations("CycleCounts.table");
  const columns = useMemo(
    () => getCycleColumns(tTable),
    [tTable],
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
