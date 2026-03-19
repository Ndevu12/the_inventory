export interface Supplier {
  id: number
  code: string
  name: string
  contact_name: string
  email: string
  phone: string
  address: string
  lead_time_days: number
  payment_terms: PaymentTerms
  payment_terms_display: string
  is_active: boolean
  notes: string
  created_at: string
  updated_at: string
}

export type PaymentTerms = "net_30" | "net_60" | "net_90" | "cod" | "prepaid"

export interface SupplierCreatePayload {
  code: string
  name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  lead_time_days?: number
  payment_terms?: PaymentTerms
  is_active?: boolean
  notes?: string
}

export interface SupplierUpdatePayload extends Partial<SupplierCreatePayload> {}

export interface SupplierListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  is_active?: string
  payment_terms?: string
}

// ─── Purchase Orders ────────────────────────────────────────────────────────

export type PurchaseOrderStatus = "draft" | "confirmed" | "received" | "cancelled"

export interface PurchaseOrderLine {
  id: number
  purchase_order: number
  product: number
  product_sku: string
  product_name: string
  quantity: number
  unit_cost: string
  line_total: string
}

export interface PurchaseOrder {
  id: number
  order_number: string
  supplier: number
  supplier_name: string
  status: PurchaseOrderStatus
  status_display: string
  order_date: string
  expected_delivery_date: string | null
  notes: string
  lines: PurchaseOrderLine[]
  total_cost: string
  created_at: string
  updated_at: string
}

export interface PurchaseOrderLinePayload {
  product: number
  quantity: number
  unit_cost: string
}

export interface PurchaseOrderCreatePayload {
  supplier: number
  order_date: string
  expected_delivery_date?: string | null
  notes?: string
  lines: PurchaseOrderLinePayload[]
}

export interface PurchaseOrderUpdatePayload {
  supplier?: number
  order_date?: string
  expected_delivery_date?: string | null
  notes?: string
}

export interface PurchaseOrderListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  status?: string
  supplier?: string
}
