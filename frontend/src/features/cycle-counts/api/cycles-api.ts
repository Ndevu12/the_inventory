import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type {
  InventoryCycle,
  InventoryCycleDetail,
  CycleCreatePayload,
  RecordCountPayload,
  ReconcilePayload,
  CycleListParams,
} from "../types/cycle-count.types";

const BASE = "/cycle-counts/";

function toQueryParams(
  params: CycleListParams,
): Record<string, string> | undefined {
  const query: Record<string, string> = {};
  if (params.page) query.page = String(params.page);
  if (params.page_size) query.page_size = String(params.page_size);
  if (params.ordering) query.ordering = params.ordering;
  if (params.search) query.search = params.search;
  if (params.status) query.status = params.status;
  if (params.location) query.location = params.location;
  return Object.keys(query).length > 0 ? query : undefined;
}

export function fetchCycles(
  params: CycleListParams = {},
): Promise<PaginatedResponse<InventoryCycle>> {
  return apiClient.get<PaginatedResponse<InventoryCycle>>(
    BASE,
    toQueryParams(params),
  );
}

export function fetchCycle(id: number): Promise<InventoryCycleDetail> {
  return apiClient.get<InventoryCycleDetail>(`${BASE}${id}/`);
}

export function startCycle(
  payload: CycleCreatePayload,
): Promise<InventoryCycleDetail> {
  return apiClient.post<InventoryCycleDetail>(`${BASE}start/`, payload);
}

export function recordCount(
  cycleId: number,
  payload: RecordCountPayload,
): Promise<InventoryCycleDetail> {
  return apiClient.post<InventoryCycleDetail>(
    `${BASE}${cycleId}/record-count/`,
    payload,
  );
}

export function completeCycle(
  cycleId: number,
): Promise<InventoryCycleDetail> {
  return apiClient.post<InventoryCycleDetail>(`${BASE}${cycleId}/complete/`);
}

export function reconcileCycle(
  cycleId: number,
  payload: ReconcilePayload,
): Promise<InventoryCycleDetail> {
  return apiClient.post<InventoryCycleDetail>(
    `${BASE}${cycleId}/reconcile/`,
    payload,
  );
}
