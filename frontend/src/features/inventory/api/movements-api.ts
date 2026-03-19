import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types";

// ─── Types ───────────────────────────────────────────────────────────────────

export type MovementType = "receive" | "issue" | "transfer" | "adjustment";

export interface StockMovementLotAllocation {
  id: number;
  lot_id: number;
  lot_number: string;
  quantity: number;
}

export interface StockMovement {
  id: number;
  product: number;
  product_sku: string;
  movement_type: MovementType;
  movement_type_display: string;
  quantity: number;
  unit_cost: string | null;
  from_location: number | null;
  from_location_name: string | null;
  to_location: number | null;
  to_location_name: string | null;
  reference: string;
  notes: string;
  lot_allocations: StockMovementLotAllocation[];
  created_at: string;
  created_by: number | null;
}

export interface StockMovementCreatePayload {
  product: number;
  movement_type: MovementType;
  quantity: number;
  from_location?: number | null;
  to_location?: number | null;
  unit_cost?: string | null;
  reference?: string;
  notes?: string;
  lot_number?: string;
  serial_number?: string;
  manufacturing_date?: string;
  expiry_date?: string;
  allocation_strategy?: "FIFO" | "LIFO";
}

export interface MovementListParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  product?: string;
  movement_type?: string;
  from_location?: string;
  to_location?: string;
  search?: string;
}

export interface SimpleProduct {
  id: number;
  sku: string;
  name: string;
}

export interface SimpleLocation {
  id: number;
  name: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

function toParams(params: MovementListParams): Record<string, string> {
  const out: Record<string, string> = {};
  if (params.page) out.page = String(params.page);
  if (params.page_size) out.page_size = String(params.page_size);
  if (params.ordering) out.ordering = params.ordering;
  if (params.product) out.product = params.product;
  if (params.movement_type) out.movement_type = params.movement_type;
  if (params.from_location) out.from_location = params.from_location;
  if (params.to_location) out.to_location = params.to_location;
  if (params.search) out.search = params.search;
  return out;
}

export function fetchMovements(params: MovementListParams = {}) {
  return apiClient.get<PaginatedResponse<StockMovement>>(
    "/stock-movements/",
    toParams(params),
  );
}

export function fetchMovement(id: number) {
  return apiClient.get<StockMovement>(`/stock-movements/${id}/`);
}

export function createMovement(payload: StockMovementCreatePayload) {
  return apiClient.post<StockMovement>("/stock-movements/", payload);
}

export function fetchProducts() {
  return apiClient.get<PaginatedResponse<SimpleProduct>>("/products/", {
    page_size: "1000",
  });
}

export function fetchLocations() {
  return apiClient.get<PaginatedResponse<SimpleLocation>>(
    "/stock-locations/",
    { page_size: "1000" },
  );
}
