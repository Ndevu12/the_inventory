import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  PurchaseOrder,
  PurchaseOrderCreatePayload,
  PurchaseOrderUpdatePayload,
  PurchaseOrderListParams,
} from "../types/procurement.types"

const BASE = "/purchase-orders"

function toParams(params: PurchaseOrderListParams): Record<string, string> {
  const out: Record<string, string> = {}
  if (params.page) out.page = String(params.page)
  if (params.page_size) out.page_size = String(params.page_size)
  if (params.ordering) out.ordering = params.ordering
  if (params.search) out.search = params.search
  if (params.status) out.status = params.status
  if (params.supplier) out.supplier = params.supplier
  return out
}

export const purchaseOrdersApi = {
  list(params?: PurchaseOrderListParams) {
    return apiClient.get<PaginatedResponse<PurchaseOrder>>(
      `${BASE}/`,
      params ? toParams(params) : undefined,
    )
  },

  get(id: number) {
    return apiClient.get<PurchaseOrder>(`${BASE}/${id}/`)
  },

  create(payload: PurchaseOrderCreatePayload) {
    return apiClient.post<PurchaseOrder>(`${BASE}/`, payload)
  },

  update(id: number, payload: PurchaseOrderUpdatePayload) {
    return apiClient.patch<PurchaseOrder>(`${BASE}/${id}/`, payload)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },

  confirm(id: number) {
    return apiClient.post<PurchaseOrder>(`${BASE}/${id}/confirm/`, {})
  },

  cancel(id: number) {
    return apiClient.post<PurchaseOrder>(`${BASE}/${id}/cancel/`, {})
  },
}
