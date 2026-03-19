import { apiClient } from "@/lib/api-client";
import type {
  DashboardSummary,
  StockByLocationData,
  MovementTrendsData,
  OrderStatusData,
  PendingReservationsData,
  ExpiringLotsData,
} from "../types/dashboard.types";

export function fetchSummary(): Promise<DashboardSummary> {
  return apiClient.get<DashboardSummary>("/dashboard/summary/");
}

export function fetchStockByLocation(): Promise<StockByLocationData> {
  return apiClient.get<StockByLocationData>("/dashboard/stock-by-location/");
}

export function fetchMovementTrends(): Promise<MovementTrendsData> {
  return apiClient.get<MovementTrendsData>("/dashboard/movement-trends/");
}

export function fetchOrderStatus(): Promise<OrderStatusData> {
  return apiClient.get<OrderStatusData>("/dashboard/order-status/");
}

export function fetchPendingReservations(): Promise<PendingReservationsData> {
  return apiClient.get<PendingReservationsData>("/dashboard/reservations/");
}

export function fetchExpiringLots(): Promise<ExpiringLotsData> {
  return apiClient.get<ExpiringLotsData>("/dashboard/expiring-lots/");
}
