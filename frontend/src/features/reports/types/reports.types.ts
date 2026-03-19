export type ValuationMethod = "weighted_average" | "latest_cost"

export type ReportPeriod = "daily" | "weekly" | "monthly"

export type VarianceType = "shortage" | "surplus" | "match"

export type ExpiryStatus = "expired" | "expiring"

// --- Stock Valuation ---

export interface StockValuationItem {
  sku: string
  product_name: string
  category: string | null
  total_quantity: number
  unit_cost: number
  total_value: number
  method: string
}

export interface StockValuationResponse {
  method: string
  total_products: number
  total_quantity: number
  total_value: string
  items: StockValuationItem[]
}

export interface StockValuationParams {
  method?: ValuationMethod
}

// --- Movement History ---

export interface MovementHistoryItem {
  id: number
  product_sku: string
  product_name: string
  movement_type: string
  quantity: number
  unit_cost: string | null
  from_location: string | null
  to_location: string | null
  reference: string
  created_at: string
  created_by: string | null
}

export interface MovementHistoryResponse {
  count: number
  results: MovementHistoryItem[]
}

export interface MovementHistoryParams {
  date_from?: string
  date_to?: string
  type?: string
}

// --- Low Stock ---

export interface LowStockItem {
  sku: string
  product_name: string
  category: string | null
  reorder_point: number
  total_stock: number
  deficit: number
}

export interface LowStockResponse {
  count: number
  results: LowStockItem[]
}

// --- Overstock ---

export interface OverstockItem {
  sku: string
  product_name: string
  category: string | null
  reorder_point: number
  total_stock: number
  threshold: number
  excess: number
}

export interface OverstockResponse {
  count: number
  threshold: number
  results: OverstockItem[]
}

export interface OverstockParams {
  threshold?: number
}

// --- Purchase Summary ---

export interface PeriodSummaryItem {
  period: string
  order_count: number
  total: string
}

export interface PurchaseSummaryResponse {
  period: string
  totals: {
    total_orders: number
    total_cost: string
  }
  results: PeriodSummaryItem[]
}

export interface PeriodSummaryParams {
  period?: ReportPeriod
  date_from?: string
  date_to?: string
}

// --- Sales Summary ---

export interface SalesSummaryResponse {
  period: string
  totals: {
    total_orders: number
    total_revenue: string
  }
  results: PeriodSummaryItem[]
}

// --- Availability ---

export interface AvailabilityItem {
  sku: string
  product_name: string
  category: string | null
  total_quantity: number
  reserved_quantity: number
  available_quantity: number
  unit_cost: string
  reserved_value: string
}

export interface AvailabilityResponse {
  count: number
  total_reserved_value: string
  results: AvailabilityItem[]
}

export interface AvailabilityParams {
  category?: string
  product?: string
}

// --- Product Expiry ---

export interface ProductExpiryItem {
  status: ExpiryStatus
  product_id: number
  sku: string
  product_name: string
  lot_number: string
  expiry_date: string
  days_to_expiry: number
  quantity_remaining: number
  quantity_received: number
  supplier: string | null
}

export interface ProductExpiryResponse {
  days_ahead: number
  expired_count: number
  expiring_count: number
  results: ProductExpiryItem[]
}

export interface ProductExpiryParams {
  days_ahead?: number
  product?: string
  location?: string
}

// --- Variances ---

export interface VarianceItem {
  id: number
  cycle_id: number
  cycle_name: string
  product_sku: string
  product_name: string
  location: string
  variance_type: VarianceType
  variance_type_display: string
  system_quantity: number
  physical_quantity: number
  variance_quantity: number
  resolution: string | null
  root_cause: string
  resolved_by: string | null
  resolved_at: string | null
  created_at: string
}

export interface VarianceResponse {
  count: number
  summary: {
    total_variances: number
    shortages: number
    surpluses: number
    matches: number
    net_variance: number
  }
  results: VarianceItem[]
}

export interface VarianceParams {
  cycle_id?: string
  product_id?: string
  variance_type?: VarianceType
}

// --- Cycle History ---

export interface CycleHistoryItem {
  id: number
  name: string
  status: string
  status_display: string
  location: string | null
  scheduled_date: string
  started_at: string | null
  completed_at: string | null
  total_lines: number
  total_variances: number
  shortages: number
  surpluses: number
  matches: number
  net_variance: number
}

export interface CycleHistoryResponse {
  count: number
  results: CycleHistoryItem[]
}

// --- Traceability ---

export interface TraceabilityChainEntry {
  action: string
  date: string
  quantity: number
  location?: string
  from?: string
  to?: string
  sales_order?: string
}

export interface TraceabilityResponse {
  product: {
    sku: string
    name: string
  }
  lot: {
    lot_number: string
    expiry_date: string | null
    supplier: string | null
  }
  chain: TraceabilityChainEntry[]
}

export interface TraceabilityParams {
  product: string
  lot: string
}

// --- Report Definition (for the index page) ---

export interface ReportDefinition {
  id: string
  name: string
  description: string
  icon: string
  path: string
}
