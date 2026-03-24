import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  Dispatch,
  DispatchCreatePayload,
  DispatchUpdatePayload,
  DispatchListParams,
  SimpleSalesOrder,
  SimpleLocation,
} from "../types/dispatch.types"

const BASE = "/dispatches"

function toParams(params: DispatchListParams): Record<string, string> {
  const out: Record<string, string> = {}
  if (params.page) out.page = String(params.page)
  if (params.page_size) out.page_size = String(params.page_size)
  if (params.ordering) out.ordering = params.ordering
  if (params.is_processed) out.is_processed = params.is_processed
  if (params.sales_order) out.sales_order = params.sales_order
  return out
}

export const dispatchesApi = {
  list(params?: DispatchListParams) {
    return apiClient.get<PaginatedResponse<Dispatch>>(
      `${BASE}/`,
      params ? toParams(params) : undefined,
    )
  },

  get(id: number) {
    return apiClient.get<Dispatch>(`${BASE}/${id}/`)
  },

  create(data: DispatchCreatePayload) {
    return apiClient.post<Dispatch>(`${BASE}/`, data)
  },

  update(id: number, data: DispatchUpdatePayload) {
    return apiClient.patch<Dispatch>(`${BASE}/${id}/`, data)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },

  process(id: number) {
    return apiClient.post<Dispatch>(`${BASE}/${id}/process/`)
  },
}

/** Confirmed orders only — dispatches can be processed only for confirmed SOs. */
export function fetchSalesOrdersForDispatch() {
  return apiClient.get<PaginatedResponse<SimpleSalesOrder>>(
    "/sales-orders/",
    { page_size: "1000", status: "confirmed" },
  )
}

export function fetchLocations() {
  return apiClient.get<PaginatedResponse<SimpleLocation>>(
    "/stock-locations/",
    { page_size: "1000" },
  )
}
