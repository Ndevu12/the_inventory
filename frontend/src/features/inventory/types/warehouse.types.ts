export interface Warehouse {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  timezone_name: string;
  address: string;
  created_at: string;
  updated_at: string;
}

export interface WarehouseFormData {
  name: string;
  description: string;
  is_active: boolean;
  timezone_name: string;
  address: string;
}

/** Matches GET /warehouses/quick-stats/ (per-facility aggregates). */
export interface WarehouseQuickStats {
  id: number;
  name: string;
  is_active: boolean;
  location_count: number;
  total_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
  capacity_total: number;
  utilization_percent: number | null;
  low_stock_line_count: number;
}
