"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
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
import { CYCLE_STATUS_VALUES } from "../helpers/cycle-constants";
import { CycleTable } from "../components/cycle-table";

export function CycleListPage() {
  const router = useRouter();
  const filters = useCycleFiltersStore();
  const t = useTranslations("CycleCounts");
  const tStatus = useTranslations("CycleCounts.status");

  const STATUS_OPTIONS: FacetedFilterOption[] = useMemo(
    () =>
      CYCLE_STATUS_VALUES.map((value) => ({
        value,
        label: tStatus(value),
      })),
    [tStatus],
  );

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
        title={t("list.title")}
        description={t("list.description")}
        actions={
          <Button onClick={() => router.push("/cycle-counts/new")}>
            <PlusIcon className="mr-2 size-4" />
            {t("list.newCycle")}
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
            title={t("list.filterStatus")}
            options={STATUS_OPTIONS}
          />
        }
      />
    </div>
  );
}
