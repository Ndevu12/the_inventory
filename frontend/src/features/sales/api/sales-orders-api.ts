import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  SalesOrder,
  SalesOrderCreatePayload,
  SalesOrderUpdatePayload,
  SalesOrderListParams,
  SimpleProduct,
  SimpleCustomer,
} from "../types/sales.types"

const BASE = "/sales-orders"

function toParams(params: SalesOrderListParams): Record<string, string> {
  const out: Record<string, string> = {}
  if (params.page) out.page = String(params.page)
  if (params.page_size) out.page_size = String(params.page_size)
  if (params.ordering) out.ordering = params.ordering
  if (params.search) out.search = params.search
  if (params.status) out.status = params.status
  if (params.customer) out.customer = params.customer
  return out
}

export const salesOrdersApi = {
  list(params?: SalesOrderListParams) {
    return apiClient.get<PaginatedResponse<SalesOrder>>(
      `${BASE}/`,
      params ? toParams(params) : undefined,
    )
  },

  get(id: number) {
    return apiClient.get<SalesOrder>(`${BASE}/${id}/`)
  },

  create(data: SalesOrderCreatePayload) {
    return apiClient.post<SalesOrder>(`${BASE}/`, data)
  },

  update(id: number, data: SalesOrderUpdatePayload) {
    return apiClient.patch<SalesOrder>(`${BASE}/${id}/`, data)
  },

  delete(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },

  confirm(id: number) {
    return apiClient.post<SalesOrder>(`${BASE}/${id}/confirm/`)
  },

  cancel(id: number) {
    return apiClient.post<SalesOrder>(`${BASE}/${id}/cancel/`)
  },
}

export function fetchProducts() {
  return apiClient.get<PaginatedResponse<SimpleProduct>>("/products/", {
    page_size: "1000",
  })
}

export function fetchCustomers() {
  return apiClient.get<PaginatedResponse<SimpleCustomer>>("/customers/", {
    page_size: "1000",
    is_active: "true",
  })
}
