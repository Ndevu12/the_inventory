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

      <KpiCards data={summary.data} isLoading={summary.isLoading} />

      <div className="grid gap-6 lg:grid-cols-2">
        <StockByLocationChart
          data={stockByLocation.data}
          isLoading={stockByLocation.isLoading}
        />
        <MovementTrendsChart
          data={movementTrends.data}
          isLoading={movementTrends.isLoading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <OrderStatusChart
          data={orderStatus.data}
          isLoading={orderStatus.isLoading}
        />
        <PendingReservationsCard
          data={reservations.data}
          isLoading={reservations.isLoading}
        />
        <ExpiringLotsCard
          data={expiringLots.data}
          isLoading={expiringLots.isLoading}
        />
      </div>
    </div>
  );
}
