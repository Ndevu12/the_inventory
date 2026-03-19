export interface StockLot {
  id: number;
  product: number;
  product_sku: string;
  lot_number: string;
  serial_number: string | null;
  manufacturing_date: string | null;
  expiry_date: string | null;
  received_date: string;
  quantity_received: number;
  quantity_remaining: number;
  is_active: boolean;
  is_expired: boolean;
  days_to_expiry: number | null;
  supplier: number | null;
  purchase_order: number | null;
  created_at: string;
  updated_at: string;
}

export interface LotListParams {
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  product?: string;
  is_active?: string;
  expiry_date__gte?: string;
  expiry_date__lte?: string;
}
