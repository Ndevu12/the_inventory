"use client";

import { DataTable } from "@/components/data-table/data-table";
import { stockRecordColumns } from "../../helpers/stock-record-columns";
import type { StockRecord } from "../../types/inventory.types";

interface StockRecordsTableProps {
  data: StockRecord[];
  pageCount?: number;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filterContent?: React.ReactNode;
}

export function StockRecordsTable({
  data,
  pageCount,
  searchValue,
  onSearchChange,
  filterContent,
}: StockRecordsTableProps) {
  return (
    <DataTable
      columns={stockRecordColumns}
      data={data}
      pageCount={pageCount}
      searchKey="product_name"
      searchPlaceholder="Search products..."
      searchValue={searchValue}
      onSearchChange={onSearchChange}
      filterContent={filterContent}
      noResultsMessage="No stock records found."
    />
  );
}
