"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { PaginationState } from "@tanstack/react-table";
import { PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import {
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table/data-table-faceted-filter";

import { useCycles } from "../hooks/use-cycles";
import { useCycleFiltersStore } from "../stores/cycle-filters-store";
import { CYCLE_STATUSES } from "../helpers/cycle-constants";
import { CycleTable } from "../components/cycle-table";

const STATUS_OPTIONS: FacetedFilterOption[] = CYCLE_STATUSES.map((s) => ({
  label: s.label,
  value: s.value,
}));

export function CycleListPage() {
  const router = useRouter();
  const filters = useCycleFiltersStore();

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: filters.pageSize,
  });

  const { data, isLoading } = useCycles({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    ordering: filters.ordering,
    search: filters.search || undefined,
    status: filters.status || undefined,
  });

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cycle Counts"
        description="Schedule and manage physical inventory count cycles."
        actions={
          <Button onClick={() => router.push("/cycle-counts/new")}>
            <PlusIcon className="mr-2 size-4" />
            New Cycle Count
          </Button>
        }
      />

      <CycleTable
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={filters.search}
        onSearchChange={filters.setSearch}
        isLoading={isLoading}
        filterContent={
          <DataTableFacetedFilter
            title="Status"
            options={STATUS_OPTIONS}
          />
        }
      />
    </div>
  );
}
