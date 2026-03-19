export interface Customer {
  id: number
  code: string
  name: string
  contact_name: string
  email: string
  phone: string
  address: string
  is_active: boolean
  notes: string
  created_at: string
  updated_at: string
}

export interface CustomerCreatePayload {
  code: string
  name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  is_active?: boolean
  notes?: string
}

export interface CustomerUpdatePayload extends Partial<CustomerCreatePayload> {}

export interface CustomerListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  is_active?: string
}

// ─── Sales Orders ────────────────────────────────────────────────────────────

export type SalesOrderStatus = "draft" | "confirmed" | "fulfilled" | "cancelled"

export interface SalesOrderLine {
  id: number
  sales_order: number
  product: number
  product_sku: string
  product_name: string
  quantity: number
  unit_price: string
  line_total: string
}

export interface SalesOrder {
  id: number
  order_number: string
  customer: number
  customer_name: string
  status: SalesOrderStatus
  status_display: string
  order_date: string
  notes: string
  lines: SalesOrderLine[]
  total_price: string
  can_fulfill: boolean
  created_at: string
  updated_at: string
}

export interface SalesOrderLinePayload {
  product: number
  quantity: number
  unit_price: string
}

export interface SalesOrderCreatePayload {
  order_number: string
  customer: number
  order_date: string
  notes?: string
  lines: SalesOrderLinePayload[]
}

export interface SalesOrderUpdatePayload {
  customer?: number
  order_date?: string
  notes?: string
}

export interface SalesOrderListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  status?: string
  customer?: string
}

export interface SimpleProduct {
  id: number
  sku: string
  name: string
}

export interface SimpleCustomer {
  id: number
  code: string
  name: string
}
