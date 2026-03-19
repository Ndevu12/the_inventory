import { useQuery } from "@tanstack/react-query"
import { reportsApi } from "../api/reports-api"
import type {
  StockValuationParams,
  MovementHistoryParams,
  OverstockParams,
  PeriodSummaryParams,
  AvailabilityParams,
  ProductExpiryParams,
  VarianceParams,
  TraceabilityParams,
} from "../types/reports.types"

export const reportKeys = {
  all: ["reports"] as const,
  stockValuation: (params?: StockValuationParams) =>
    [...reportKeys.all, "stock-valuation", params] as const,
  movementHistory: (params?: MovementHistoryParams) =>
    [...reportKeys.all, "movement-history", params] as const,
  lowStock: () => [...reportKeys.all, "low-stock"] as const,
  overstock: (params?: OverstockParams) =>
    [...reportKeys.all, "overstock", params] as const,
  purchaseSummary: (params?: PeriodSummaryParams) =>
    [...reportKeys.all, "purchase-summary", params] as const,
  salesSummary: (params?: PeriodSummaryParams) =>
    [...reportKeys.all, "sales-summary", params] as const,
  availability: (params?: AvailabilityParams) =>
    [...reportKeys.all, "availability", params] as const,
  productExpiry: (params?: ProductExpiryParams) =>
    [...reportKeys.all, "product-expiry", params] as const,
  variances: (params?: VarianceParams) =>
    [...reportKeys.all, "variances", params] as const,
  cycleHistory: () => [...reportKeys.all, "cycle-history"] as const,
  traceability: (params: TraceabilityParams) =>
    [...reportKeys.all, "traceability", params] as const,
}

export function useStockValuation(params?: StockValuationParams) {
  return useQuery({
    queryKey: reportKeys.stockValuation(params),
    queryFn: () => reportsApi.stockValuation(params),
  })
}

export function useMovementHistory(params?: MovementHistoryParams) {
  return useQuery({
    queryKey: reportKeys.movementHistory(params),
    queryFn: () => reportsApi.movementHistory(params),
  })
}

export function useLowStock() {
  return useQuery({
    queryKey: reportKeys.lowStock(),
    queryFn: () => reportsApi.lowStock(),
  })
}

export function useOverstock(params?: OverstockParams) {
  return useQuery({
    queryKey: reportKeys.overstock(params),
    queryFn: () => reportsApi.overstock(params),
  })
}

export function usePurchaseSummary(params?: PeriodSummaryParams) {
  return useQuery({
    queryKey: reportKeys.purchaseSummary(params),
    queryFn: () => reportsApi.purchaseSummary(params),
  })
}

export function useSalesSummary(params?: PeriodSummaryParams) {
  return useQuery({
    queryKey: reportKeys.salesSummary(params),
    queryFn: () => reportsApi.salesSummary(params),
  })
}

export function useAvailability(params?: AvailabilityParams) {
  return useQuery({
    queryKey: reportKeys.availability(params),
    queryFn: () => reportsApi.availability(params),
  })
}

export function useProductExpiry(params?: ProductExpiryParams) {
  return useQuery({
    queryKey: reportKeys.productExpiry(params),
    queryFn: () => reportsApi.productExpiry(params),
  })
}

export function useVariances(params?: VarianceParams) {
  return useQuery({
    queryKey: reportKeys.variances(params),
    queryFn: () => reportsApi.variances(params),
  })
}

export function useCycleHistory() {
  return useQuery({
    queryKey: reportKeys.cycleHistory(),
    queryFn: () => reportsApi.cycleHistory(),
  })
}

export function useTraceability(params: TraceabilityParams) {
  return useQuery({
    queryKey: reportKeys.traceability(params),
    queryFn: () => reportsApi.traceability(params),
    enabled: !!params.product && !!params.lot,
  })
}
