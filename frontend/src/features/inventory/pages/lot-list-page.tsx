"use client";

import * as React from "react";
import type { PaginationState, SortingState } from "@tanstack/react-table";
import { PageHeader } from "@/components/layout";
import { LoadingSkeleton } from "@/components/layout/loading-skeleton";
import { useLots } from "../hooks/use-lots";
import { LotTable } from "../components/lots/lot-table";
import type { LotListParams } from "../types/lot.types";

export function LotListPage() {
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [search, setSearch] = React.useState("");
  const [activeFilter, setActiveFilter] = React.useState<string | undefined>(
    undefined,
  );

  const params = React.useMemo<LotListParams>(() => {
    const p: LotListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
    };

    if (search) p.search = search;
    if (activeFilter !== undefined) p.is_active = activeFilter;

    if (sorting.length > 0) {
      const { id, desc } = sorting[0];
      const fieldMap: Record<string, string> = {
        received_date: "received_date",
        expiry_date: "expiry_date",
        quantity_remaining: "quantity_remaining",
        lot_number: "created_at",
      };
      const field = fieldMap[id] ?? id;
      p.ordering = desc ? `-${field}` : field;
    }

    return p;
  }, [pagination, sorting, search, activeFilter]);

  const { data, isLoading } = useLots(params);

  const pageCount = data
    ? Math.ceil(data.count / pagination.pageSize)
    : -1;

  function handleSearchChange(value: string) {
    setSearch(value);
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }

  function handleActiveFilterChange(value: string | undefined) {
    setActiveFilter(value);
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Lots"
        description="View and filter lot/batch records with expiry tracking."
      />
      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <LotTable
          data={data?.results ?? []}
          pageCount={pageCount}
          pagination={pagination}
          onPaginationChange={setPagination}
          sorting={sorting}
          onSortingChange={setSorting}
          searchValue={search}
          onSearchChange={handleSearchChange}
          activeFilter={activeFilter}
          onActiveFilterChange={handleActiveFilterChange}
        />
      )}
    </div>
  );
}
