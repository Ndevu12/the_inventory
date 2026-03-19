import { apiClient } from "@/lib/api-client"
import type {
  StockValuationResponse,
  StockValuationParams,
  MovementHistoryResponse,
  MovementHistoryParams,
  LowStockResponse,
  OverstockResponse,
  OverstockParams,
  PurchaseSummaryResponse,
  PeriodSummaryParams,
  SalesSummaryResponse,
  AvailabilityResponse,
  AvailabilityParams,
  ProductExpiryResponse,
  ProductExpiryParams,
  VarianceResponse,
  VarianceParams,
  CycleHistoryResponse,
  TraceabilityResponse,
  TraceabilityParams,
} from "../types/reports.types"

const BASE = "/reports"

function toStringRecord(
  params: Record<string, string | number | undefined>,
): Record<string, string> {
  const result: Record<string, string> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      result[key] = String(value)
    }
  }
  return result
}

export const reportsApi = {
  stockValuation(params?: StockValuationParams) {
    return apiClient.get<StockValuationResponse>(
      `${BASE}/stock-valuation/`,
      toStringRecord({ ...params }),
    )
  },

  movementHistory(params?: MovementHistoryParams) {
    return apiClient.get<MovementHistoryResponse>(
      `${BASE}/movement-history/`,
      toStringRecord({ ...params }),
    )
  },

  lowStock() {
    return apiClient.get<LowStockResponse>(`${BASE}/low-stock/`)
  },

  overstock(params?: OverstockParams) {
    return apiClient.get<OverstockResponse>(
      `${BASE}/overstock/`,
      toStringRecord({ ...params }),
    )
  },

  purchaseSummary(params?: PeriodSummaryParams) {
    return apiClient.get<PurchaseSummaryResponse>(
      `${BASE}/purchase-summary/`,
      toStringRecord({ ...params }),
    )
  },

  salesSummary(params?: PeriodSummaryParams) {
    return apiClient.get<SalesSummaryResponse>(
      `${BASE}/sales-summary/`,
      toStringRecord({ ...params }),
    )
  },

  availability(params?: AvailabilityParams) {
    return apiClient.get<AvailabilityResponse>(
      `${BASE}/availability/`,
      toStringRecord({ ...params }),
    )
  },

  productExpiry(params?: ProductExpiryParams) {
    return apiClient.get<ProductExpiryResponse>(
      `${BASE}/product-expiry/`,
      toStringRecord({ ...params }),
    )
  },

  variances(params?: VarianceParams) {
    return apiClient.get<VarianceResponse>(
      `${BASE}/variances/`,
      toStringRecord({ ...params }),
    )
  },

  cycleHistory() {
    return apiClient.get<CycleHistoryResponse>(`${BASE}/cycle-history/`)
  },

  traceability(params: TraceabilityParams) {
    return apiClient.get<TraceabilityResponse>(
      `${BASE}/product-traceability/`,
      toStringRecord({ ...params }),
    )
  },
}
