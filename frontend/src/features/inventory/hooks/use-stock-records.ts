import { useQuery, keepPreviousData } from "@tanstack/react-query";
import {
  fetchStockRecords,
  fetchLowStockRecords,
} from "../api/stock-records-api";
import type { StockRecordListParams } from "../types/inventory.types";

export const stockRecordKeys = {
  all: ["stock-records"] as const,
  lists: () => [...stockRecordKeys.all, "list"] as const,
  list: (params?: StockRecordListParams) =>
    [...stockRecordKeys.lists(), params ?? {}] as const,
  lowStock: () => [...stockRecordKeys.all, "low-stock"] as const,
};

export function useStockRecords(params?: StockRecordListParams) {
  return useQuery({
    queryKey: stockRecordKeys.list(params),
    queryFn: () => fetchStockRecords(params),
    placeholderData: keepPreviousData,
  });
}

export function useLowStockRecords() {
  return useQuery({
    queryKey: stockRecordKeys.lowStock(),
    queryFn: fetchLowStockRecords,
  });
}
