import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type { StockLot, LotListParams } from "../types/lot.types";

const BASE_PATH = "/stock-lots/";

export function fetchLots(
  params: LotListParams = {},
): Promise<PaginatedResponse<StockLot>> {
  const query: Record<string, string> = {};

  if (params.page) query.page = String(params.page);
  if (params.page_size) query.page_size = String(params.page_size);
  if (params.search) query.search = params.search;
  if (params.ordering) query.ordering = params.ordering;
  if (params.product) query.product = params.product;
  if (params.is_active !== undefined) query.is_active = params.is_active;
  if (params.expiry_date__gte) query.expiry_date__gte = params.expiry_date__gte;
  if (params.expiry_date__lte) query.expiry_date__lte = params.expiry_date__lte;

  return apiClient.get<PaginatedResponse<StockLot>>(BASE_PATH, query);
}

export function fetchLot(id: number): Promise<StockLot> {
  return apiClient.get<StockLot>(`${BASE_PATH}${id}/`);
}
