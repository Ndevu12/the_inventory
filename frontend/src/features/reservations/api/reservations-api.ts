import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import type {
  StockReservation,
  CreateReservationPayload,
  ReservationListParams,
} from "../types/reservation.types";

const BASE = "/reservations/";

function toQueryParams(
  params: ReservationListParams,
): Record<string, string> | undefined {
  const query: Record<string, string> = {};
  if (params.page) query.page = String(params.page);
  if (params.page_size) query.page_size = String(params.page_size);
  if (params.ordering) query.ordering = params.ordering;
  if (params.search) query.search = params.search;
  if (params.status) query.status = params.status;
  if (params.product) query.product = params.product;
  if (params.location) query.location = params.location;
  return Object.keys(query).length > 0 ? query : undefined;
}

export function fetchReservations(
  params: ReservationListParams = {},
): Promise<PaginatedResponse<StockReservation>> {
  return apiClient.get<PaginatedResponse<StockReservation>>(
    BASE,
    toQueryParams(params),
  );
}

export function fetchReservation(id: number): Promise<StockReservation> {
  return apiClient.get<StockReservation>(`${BASE}${id}/`);
}

export function createReservation(
  payload: CreateReservationPayload,
): Promise<StockReservation> {
  return apiClient.post<StockReservation>(BASE, payload);
}

export function fulfillReservation(id: number): Promise<StockReservation> {
  return apiClient.post<StockReservation>(`${BASE}${id}/fulfill/`);
}

export function cancelReservation(id: number): Promise<StockReservation> {
  return apiClient.post<StockReservation>(`${BASE}${id}/cancel/`);
}
