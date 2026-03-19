import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  GoodsReceivedNote,
  GRNCreatePayload,
  GRNUpdatePayload,
  GRNListParams,
  SimplePurchaseOrder,
  SimpleLocation,
} from "../types/grn.types"

const BASE = "/goods-received-notes"

function toParams(params: GRNListParams): Record<string, string> {
  const out: Record<string, string> = {}
  if (params.page) out.page = String(params.page)
  if (params.page_size) out.page_size = String(params.page_size)
  if (params.ordering) out.ordering = params.ordering
  if (params.is_processed) out.is_processed = params.is_processed
  if (params.purchase_order) out.purchase_order = params.purchase_order
  return out
}

export const grnApi = {
  list(params?: GRNListParams) {
    return apiClient.get<PaginatedResponse<GoodsReceivedNote>>(
      `${BASE}/`,
      params ? toParams(params) : undefined,
    )
  },

  get(id: number) {
    return apiClient.get<GoodsReceivedNote>(`${BASE}/${id}/`)
  },

  create(data: GRNCreatePayload) {
    return apiClient.post<GoodsReceivedNote>(`${BASE}/`, data)
  },

  update(id: number, data: GRNUpdatePayload) {
    return apiClient.patch<GoodsReceivedNote>(`${BASE}/${id}/`, data)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },

  receive(id: number) {
    return apiClient.post<GoodsReceivedNote>(`${BASE}/${id}/receive/`)
  },
}

export function fetchPurchaseOrders() {
  return apiClient.get<PaginatedResponse<SimplePurchaseOrder>>(
    "/purchase-orders/",
    { page_size: "1000" },
  )
}

export function fetchLocations() {
  return apiClient.get<PaginatedResponse<SimpleLocation>>(
    "/stock-locations/",
    { page_size: "1000" },
  )
}
