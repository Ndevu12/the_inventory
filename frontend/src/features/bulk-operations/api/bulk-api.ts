import { apiClient } from "@/lib/api-client";
import type { SimpleProduct, SimpleLocation } from "../../inventory/api/movements-api";
import type { PaginatedResponse } from "@/types";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface BulkTransferItem {
  product_id: number;
  quantity: number;
}

export interface BulkTransferPayload {
  items: BulkTransferItem[];
  from_location: number;
  to_location: number;
  reference?: string;
  notes?: string;
  fail_fast?: boolean;
}

export interface BulkAdjustmentItem {
  product_id: number;
  new_quantity: number;
}

export interface BulkAdjustmentPayload {
  items: BulkAdjustmentItem[];
  location: number;
  notes?: string;
  fail_fast?: boolean;
}

export interface BulkRevalueItem {
  product_id: number;
  new_unit_cost: string;
}

export interface BulkRevaluePayload {
  items: BulkRevalueItem[];
  fail_fast?: boolean;
}

export interface BulkItemError {
  index: number;
  product_id: number;
  error: string;
}

export interface BulkItemResult {
  index: number;
  product_id: number;
  status: string;
  [key: string]: unknown;
}

export interface BulkOperationResult {
  success_count: number;
  failure_count: number;
  total_count: number;
  errors: BulkItemError[];
  results: BulkItemResult[];
}

// ─── API Calls ───────────────────────────────────────────────────────────────

const BASE = "/bulk-operations";

export const bulkApi = {
  transfer(payload: BulkTransferPayload) {
    return apiClient.post<BulkOperationResult>(`${BASE}/transfer/`, payload);
  },

  adjust(payload: BulkAdjustmentPayload) {
    return apiClient.post<BulkOperationResult>(`${BASE}/adjust/`, payload);
  },

  revalue(payload: BulkRevaluePayload) {
    return apiClient.post<BulkOperationResult>(`${BASE}/revalue/`, payload);
  },
};

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
