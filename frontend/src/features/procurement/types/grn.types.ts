export interface GoodsReceivedNote {
  id: number
  grn_number: string
  purchase_order: number
  purchase_order_number: string
  received_date: string
  location: number
  location_name: string
  notes: string
  is_processed: boolean
  created_at: string
  updated_at: string
}

export interface GRNCreatePayload {
  grn_number: string
  purchase_order: number
  received_date: string
  location: number
  notes?: string
}

export interface GRNUpdatePayload extends Partial<GRNCreatePayload> {}

export interface GRNListParams {
  page?: number
  page_size?: number
  ordering?: string
  is_processed?: string
  purchase_order?: string
}

export interface SimplePurchaseOrder {
  id: number
  order_number: string
  supplier_name: string
  status: string
  status_display: string
}

export interface SimpleLocation {
  id: number
  name: string
}
