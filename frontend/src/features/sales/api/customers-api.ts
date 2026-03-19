import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  Customer,
  CustomerCreatePayload,
  CustomerUpdatePayload,
} from "../types/sales.types"

const BASE = "/customers"

export const customersApi = {
  list(params?: Record<string, string>) {
    return apiClient.get<PaginatedResponse<Customer>>(`${BASE}/`, params)
  },

  get(id: number) {
    return apiClient.get<Customer>(`${BASE}/${id}/`)
  },

  create(data: CustomerCreatePayload) {
    return apiClient.post<Customer>(`${BASE}/`, data)
  },

  update(id: number, data: CustomerUpdatePayload) {
    return apiClient.patch<Customer>(`${BASE}/${id}/`, data)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },
}
