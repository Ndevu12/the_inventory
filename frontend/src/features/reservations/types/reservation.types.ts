export type ReservationStatus =
  | "pending"
  | "confirmed"
  | "fulfilled"
  | "cancelled"
  | "expired";

export interface StockReservation {
  id: number;
  product: number;
  product_sku: string;
  product_name: string;
  location: number;
  location_name: string;
  quantity: number;
  sales_order: number | null;
  sales_order_number: string | null;
  reserved_by: number | null;
  reserved_by_username: string | null;
  status: ReservationStatus;
  status_display: string;
  expires_at: string | null;
  fulfilled_movement: number | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface CreateReservationPayload {
  product: number;
  location: number;
  quantity: number;
  sales_order?: number | null;
  notes?: string;
}

export interface ReservationListParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  search?: string;
  status?: string;
  product?: string;
  location?: string;
}
