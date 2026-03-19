import { useQuery } from "@tanstack/react-query";
import {
  fetchSummary,
  fetchStockByLocation,
  fetchMovementTrends,
  fetchOrderStatus,
  fetchPendingReservations,
  fetchExpiringLots,
} from "../api/dashboard-api";

export const dashboardKeys = {
  all: ["dashboard"] as const,
  summary: () => [...dashboardKeys.all, "summary"] as const,
  stockByLocation: () => [...dashboardKeys.all, "stock-by-location"] as const,
  movementTrends: () => [...dashboardKeys.all, "movement-trends"] as const,
  orderStatus: () => [...dashboardKeys.all, "order-status"] as const,
  reservations: () => [...dashboardKeys.all, "reservations"] as const,
  expiringLots: () => [...dashboardKeys.all, "expiring-lots"] as const,
};

export function useSummary() {
  return useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: fetchSummary,
  });
}

export function useStockByLocation() {
  return useQuery({
    queryKey: dashboardKeys.stockByLocation(),
    queryFn: fetchStockByLocation,
  });
}

export function useMovementTrends() {
  return useQuery({
    queryKey: dashboardKeys.movementTrends(),
    queryFn: fetchMovementTrends,
  });
}

export function useOrderStatus() {
  return useQuery({
    queryKey: dashboardKeys.orderStatus(),
    queryFn: fetchOrderStatus,
  });
}

export function usePendingReservations() {
  return useQuery({
    queryKey: dashboardKeys.reservations(),
    queryFn: fetchPendingReservations,
  });
}

export function useExpiringLots() {
  return useQuery({
    queryKey: dashboardKeys.expiringLots(),
    queryFn: fetchExpiringLots,
  });
}
