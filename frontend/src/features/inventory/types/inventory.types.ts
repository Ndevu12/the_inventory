export interface Product {
  id: number
  sku: string
  name: string
  description: string
  category: number | null
  category_name: string | null
  unit_of_measure: string
  unit_of_measure_display: string
  unit_cost: string
  reorder_point: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  slug: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StockRecord {
  id: number
  product: number
  product_sku: string
  product_name: string
  location: number
  location_name: string
  quantity: number
  reserved_quantity: number
  available_quantity: number
  is_low_stock: boolean
  created_at: string
  updated_at: string
}

export interface StockMovement {
  id: number
  product: number
  product_sku: string
  movement_type: string
  movement_type_display: string
  quantity: number
  unit_cost: string
  from_location: number | null
  from_location_name: string | null
  to_location: number | null
  to_location_name: string | null
  reference: string
  notes: string
  lot_allocations: StockMovementLot[]
  created_at: string
  created_by: number | null
}

export interface StockMovementLot {
  id: number
  lot_id: number
  lot_number: string
  quantity: number
}

export interface StockLot {
  id: number
  product: number
  product_sku: string
  lot_number: string
  serial_number: string
  manufacturing_date: string | null
  expiry_date: string | null
  received_date: string | null
  quantity_received: number
  quantity_remaining: number
  is_active: boolean
  is_expired: boolean
  days_to_expiry: number | null
  supplier: number | null
  purchase_order: number | null
  created_at: string
  updated_at: string
}

export interface ProductFormValues {
  sku: string
  name: string
  description: string
  category: number | null
  unit_of_measure: string
  unit_cost: number
  reorder_point: number
  tracking_mode: string
  is_active: boolean
}
