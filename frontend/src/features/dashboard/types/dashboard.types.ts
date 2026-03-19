export interface DashboardSummary {
  total_products: number;
  total_locations: number;
  low_stock_count: number;
  total_stock_records: number;
  total_reserved: number;
  total_available: number;
  purchase_orders: number;
  sales_orders: number;
  reserved_stock_value: string;
}

export interface StockByLocationData {
  labels: string[];
  data: number[];
  reserved: number[];
  available: number[];
}

export interface ChartDataset {
  labels: string[];
  data: number[];
}

export interface MovementTrendsData {
  labels: string[];
  data: number[];
}

export interface OrderStatusData {
  purchase_orders: ChartDataset;
  sales_orders: ChartDataset;
}

export interface ReservationBreakdown {
  count: number;
  units: number;
}

export interface PendingReservationsData {
  reservation_count: number;
  total_units: number;
  total_value: number;
  pending: ReservationBreakdown;
  confirmed: ReservationBreakdown;
}

export interface ExpiringLot {
  id: number;
  lot_number: string;
  product_sku: string;
  product_name: string;
  expiry_date: string;
  days_to_expiry: number | null;
  quantity_remaining: number;
}

export interface ExpiringLotsData {
  has_lot_data: boolean;
  expiring_lots: ExpiringLot[];
}
