export type CycleStatus = "scheduled" | "in_progress" | "completed" | "reconciled";

export type VarianceType = "shortage" | "surplus" | "match";

export type VarianceResolution = "accepted" | "investigating" | "rejected";

export interface CycleCountLine {
  id: number;
  cycle: number;
  product: number;
  product_sku: string;
  product_name: string;
  location: number;
  location_name: string;
  system_quantity: number;
  counted_quantity: number | null;
  counted_by: number | null;
  counted_by_username: string | null;
  counted_at: string | null;
  variance: number | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryVariance {
  id: number;
  cycle: number;
  count_line: number;
  product: number;
  product_sku: string;
  product_name: string;
  location: number;
  location_name: string;
  variance_type: VarianceType;
  variance_type_display: string;
  system_quantity: number;
  physical_quantity: number;
  variance_quantity: number;
  resolution: VarianceResolution | null;
  resolution_display: string | null;
  adjustment_movement: number | null;
  resolved_by: number | null;
  resolved_by_username: string | null;
  resolved_at: string | null;
  root_cause: string;
  created_at: string;
  updated_at: string;
}

export interface VarianceSummary {
  shortages: number;
  surpluses: number;
  matches: number;
  uncounted: number;
  total_lines: number;
}

export interface InventoryCycle {
  id: number;
  name: string;
  location: number | null;
  location_name: string | null;
  status: CycleStatus;
  status_display: string;
  scheduled_date: string;
  started_at: string | null;
  completed_at: string | null;
  started_by: number | null;
  started_by_username: string | null;
  total_lines: number;
  counted_lines: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryCycleDetail extends InventoryCycle {
  lines: CycleCountLine[];
  variances: InventoryVariance[];
  variance_summary: VarianceSummary;
}

export interface CycleCreatePayload {
  name: string;
  location?: number | null;
  scheduled_date: string;
  notes?: string;
}

export interface RecordCountPayload {
  product: number;
  location: number;
  counted_quantity: number;
  notes?: string;
}

export interface ReconcilePayload {
  resolutions: Record<string, { resolution: VarianceResolution; root_cause?: string }>;
}

export interface CycleListParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  search?: string;
  status?: string;
  location?: string;
}
