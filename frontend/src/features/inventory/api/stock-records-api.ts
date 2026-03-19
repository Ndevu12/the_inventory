import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type {
  StockRecord,
  StockRecordListParams,
} from "../types/inventory.types";

const BASE = "/stock-records";

export function fetchStockRecords(
  params?: StockRecordListParams,
): Promise<PaginatedResponse<StockRecord>> {
  return apiClient.get<PaginatedResponse<StockRecord>>(
    `${BASE}/`,
    params as Record<string, string>,
  );
}

export function fetchStockRecord(id: number): Promise<StockRecord> {
  return apiClient.get<StockRecord>(`${BASE}/${id}/`);
}

export function fetchLowStockRecords(): Promise<StockRecord[]> {
  return apiClient.get<StockRecord[]>(`${BASE}/low_stock/`);
}
