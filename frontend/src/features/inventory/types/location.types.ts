import type { Warehouse } from "./warehouse.types";

export interface StockLocation {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  max_capacity: number | null;
  warehouse: Warehouse | null;
  warehouse_id: number | null;
  current_utilization: number;
  remaining_capacity: number | null;
  /** treebeard MP_Node depth (1 = root). */
  depth?: number;
  /** Immediate parent location id, or null for roots. */
  parent_id?: number | null;
  /** Materialised path segment for stable tree ordering (MP_Node). */
  materialized_path?: string;
  /** Present on GET detail only — root → parent of self for expand-ancestor UX. */
  ancestor_ids?: number[] | null;
  created_at: string;
  updated_at: string;
}

export interface StockLocationFormData {
  name: string;
  description: string;
  is_active: boolean;
  max_capacity: number | null;
  /** Omit or null for retail / store-only locations (no facility row). */
  warehouse_id?: number | null;
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
