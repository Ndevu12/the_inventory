export interface Dispatch {
  id: number
  dispatch_number: string
  sales_order: number
  sales_order_number: string
  dispatch_date: string
  from_location: number
  from_location_name: string
  notes: string
  is_processed: boolean
  created_at: string
  updated_at: string
}

export interface DispatchCreatePayload {
  /** Omit or leave empty; the API assigns a unique dispatch number (DSP- prefix). */
  dispatch_number?: string
  sales_order: number
  dispatch_date: string
  from_location: number
  notes?: string
}

export interface DispatchUpdatePayload extends Partial<DispatchCreatePayload> {}

export interface DispatchListParams {
  page?: number
  page_size?: number
  ordering?: string
  is_processed?: string
  sales_order?: string
}

export interface SimpleSalesOrder {
  id: number
  order_number: string
  customer_name: string
  status: string
  status_display: string
}

export interface SimpleLocation {
  id: number
  name: string
}

export interface DispatchFulfillmentLine {
  line_id: number
  product_id: number
  product_sku: string
  product_name: string | null
  ordered_quantity: number
  available_quantity: number
  issue_now_quantity: number
}

export interface DispatchFulfillmentPreview {
  from_location: { id: number; name: string }
  sales_order_id: number
  lines: DispatchFulfillmentLine[]
  can_full_dispatch: boolean
  total_issue_if_available_only: number
}
