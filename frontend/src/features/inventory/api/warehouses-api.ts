import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type {
  Warehouse,
  WarehouseFormData,
  WarehouseQuickStats,
} from "../types/warehouse.types";

const BASE = "/warehouses";

export const warehousesApi = {
  list(params?: Record<string, string>) {
    return apiClient.get<PaginatedResponse<Warehouse>>(`${BASE}/`, params);
  },

  quickStats() {
    return apiClient.get<WarehouseQuickStats[]>(`${BASE}/quick-stats/`);
  },

  get(id: number) {
    return apiClient.get<Warehouse>(`${BASE}/${id}/`);
  },

  create(data: WarehouseFormData) {
    return apiClient.post<Warehouse>(`${BASE}/`, data);
  },

  update(id: number, data: Partial<WarehouseFormData>) {
    return apiClient.patch<Warehouse>(`${BASE}/${id}/`, data);
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`);
  },
};
