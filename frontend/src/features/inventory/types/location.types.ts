export interface StockLocation {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  max_capacity: number | null;
  current_utilization: number;
  remaining_capacity: number | null;
  created_at: string;
  updated_at: string;
}

export interface StockLocationFormData {
  name: string;
  description: string;
  is_active: boolean;
  max_capacity: number | null;
}

export interface StockRecordAtLocation {
  id: number;
  product: number;
  location: number;
  product_sku: string;
  product_name: string;
  location_name: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  is_low_stock: boolean;
  last_updated: string;
}
