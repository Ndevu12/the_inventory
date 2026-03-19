import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types"
import type {
  Supplier,
  SupplierCreatePayload,
  SupplierUpdatePayload,
  SupplierListParams,
} from "../types/procurement.types"

const BASE = "/suppliers"

function toQueryParams(params?: SupplierListParams): Record<string, string> | undefined {
  if (!params) return undefined
  const out: Record<string, string> = {}
  if (params.page != null) out.page = String(params.page)
  if (params.page_size != null) out.page_size = String(params.page_size)
  if (params.search) out.search = params.search
  if (params.ordering) out.ordering = params.ordering
  if (params.is_active) out.is_active = params.is_active
  if (params.payment_terms) out.payment_terms = params.payment_terms
  return Object.keys(out).length > 0 ? out : undefined
}

export const suppliersApi = {
  list(params?: SupplierListParams) {
    return apiClient.get<PaginatedResponse<Supplier>>(
      `${BASE}/`,
      toQueryParams(params)
    )
  },

  get(id: number) {
    return apiClient.get<Supplier>(`${BASE}/${id}/`)
  },

  create(payload: SupplierCreatePayload) {
    return apiClient.post<Supplier>(`${BASE}/`, payload)
  },

  update(id: number, payload: SupplierUpdatePayload) {
    return apiClient.patch<Supplier>(`${BASE}/${id}/`, payload)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },
}
