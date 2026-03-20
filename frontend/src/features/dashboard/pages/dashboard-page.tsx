"use client";

import {
  useSummary,
  useStockByLocation,
  useMovementTrends,
  useOrderStatus,
  usePendingReservations,
  useExpiringLots,
} from "../hooks/use-dashboard";
import { KpiCards } from "../components/kpi-cards";
import { StockByLocationChart } from "../components/stock-by-location-chart";
import { MovementTrendsChart } from "../components/movement-trends-chart";
import { OrderStatusChart } from "../components/order-status-chart";
import { PendingReservationsCard } from "../components/pending-reservations-card";
import { ExpiringLotsCard } from "../components/expiring-lots-card";

export function DashboardPage() {
  const summary = useSummary();
  const stockByLocation = useStockByLocation();
  const movementTrends = useMovementTrends();
  const orderStatus = useOrderStatus();
  const reservations = usePendingReservations();
  const expiringLots = useExpiringLots();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your inventory, orders, and operations.
        </p>
      </div>

      <KpiCards
        data={summary.data}
        isLoading={summary.isLoading}
        isError={summary.isError}
        error={summary.error}
        onRetry={() => void summary.refetch()}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <StockByLocationChart
          data={stockByLocation.data}
          isLoading={stockByLocation.isLoading}
          isError={stockByLocation.isError}
          error={stockByLocation.error}
          onRetry={() => void stockByLocation.refetch()}
        />
        <MovementTrendsChart
          data={movementTrends.data}
          isLoading={movementTrends.isLoading}
          isError={movementTrends.isError}
          error={movementTrends.error}
          onRetry={() => void movementTrends.refetch()}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <OrderStatusChart
          data={orderStatus.data}
          isLoading={orderStatus.isLoading}
          isError={orderStatus.isError}
          error={orderStatus.error}
          onRetry={() => void orderStatus.refetch()}
        />
        <PendingReservationsCard
          data={reservations.data}
          isLoading={reservations.isLoading}
          isError={reservations.isError}
          error={reservations.error}
          onRetry={() => void reservations.refetch()}
        />
        <ExpiringLotsCard
          data={expiringLots.data}
          isLoading={expiringLots.isLoading}
          isError={expiringLots.isError}
          error={expiringLots.error}
          onRetry={() => void expiringLots.refetch()}
        />
      </div>
    </div>
  );
}
