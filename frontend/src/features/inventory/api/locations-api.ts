import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type {
  StockLocation,
  StockLocationFormData,
  StockRecordAtLocation,
} from "../types/location.types";

const BASE = "/stock-locations";

export const locationsApi = {
  list(params?: Record<string, string>) {
    return apiClient.get<PaginatedResponse<StockLocation>>(`${BASE}/`, params);
  },

  get(id: number) {
    return apiClient.get<StockLocation>(`${BASE}/${id}/`);
  },

  create(data: StockLocationFormData) {
    return apiClient.post<StockLocation>(`${BASE}/`, data);
  },

  update(id: number, data: Partial<StockLocationFormData>) {
    return apiClient.patch<StockLocation>(`${BASE}/${id}/`, data);
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`);
  },

  stockAt(id: number) {
    return apiClient.get<StockRecordAtLocation[]>(`${BASE}/${id}/stock/`);
  },
};
