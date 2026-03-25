export interface DashboardSummary {
  total_products: number;
  total_locations: number;
  active_warehouses: number;
  locations_with_warehouse: number;
  locations_retail_site: number;
  low_stock_count: number;
  total_stock_records: number;
  total_reserved: number;
  total_available: number;
  purchase_orders: number;
  sales_orders: number;
  reserved_stock_value: string;
}

/** Rolled-up stock for a warehouse or a single neutral “retail site” bucket. */
export interface StockBySiteRow {
  warehouse_id: number | null;
  label: string;
  kind: "warehouse" | "retail_site";
  total_quantity: number;
  reserved: number;
  available: number;
}

export interface StockByLocationData {
  labels: string[];
  data: number[];
  reserved: number[];
  available: number[];
  by_site: StockBySiteRow[];
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
