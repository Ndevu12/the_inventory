"use client";

import * as React from "react";
import { AlertTriangleIcon } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useStockRecords } from "../hooks/use-stock-records";
import { StockRecordsTable } from "../components/stock-records/stock-records-table";
import type { StockRecordListParams } from "../types/inventory.types";

export function StockRecordsPage() {
  const [search, setSearch] = React.useState("");
  const [lowStockOnly, setLowStockOnly] = React.useState(false);

  const params = React.useMemo<StockRecordListParams>(() => {
    const p: StockRecordListParams = {};
    if (search) p.product = search;
    return p;
  }, [search]);

  const { data, isLoading, isError, error } = useStockRecords(params);

  const filteredResults = React.useMemo(() => {
    if (!data?.results) return [];
    if (lowStockOnly) return data.results.filter((r) => r.is_low_stock);
    return data.results;
  }, [data?.results, lowStockOnly]);

  const lowStockCount = React.useMemo(
    () => data?.results.filter((r) => r.is_low_stock).length ?? 0,
    [data?.results],
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Stock Records"
          description="Current stock levels across all locations"
        />
        <div className="rounded-md border border-destructive/50 bg-destructive/5 p-6 text-center">
          <p className="text-sm text-destructive">
            Failed to load stock records
            {error instanceof Error ? `: ${error.message}` : "."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Records"
        description="Current stock levels across all locations"
        actions={
          <Button
            variant={lowStockOnly ? "default" : "outline"}
            size="sm"
            onClick={() => setLowStockOnly((prev) => !prev)}
            className={cn(lowStockOnly && "gap-1.5")}
          >
            <AlertTriangleIcon className="size-4" />
            Low Stock{lowStockCount > 0 ? ` (${lowStockCount})` : ""}
          </Button>
        }
      />

      <StockRecordsTable
        data={filteredResults}
        searchValue={search}
        onSearchChange={setSearch}
      />
    </div>
  );
}
