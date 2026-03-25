export type AuditAction =
  | "stock_received"
  | "stock_issued"
  | "stock_transferred"
  | "stock_adjusted"
  | "reservation_created"
  | "reservation_fulfilled"
  | "reservation_cancelled"
  | "cycle_count_started"
  | "cycle_count_reconciled"
  | "bulk_operation"
  | "product_created"
  | "product_updated"
  | "product_deleted"
  | "category_created"
  | "category_updated"
  | "category_deleted"
  | "warehouse_created"
  | "warehouse_updated"
  | "warehouse_deleted"
  | "location_created"
  | "location_updated"
  | "location_deleted"
  | "customer_created"
  | "customer_updated"
  | "customer_deleted"
  | "supplier_created"
  | "supplier_updated"
  | "supplier_deleted"
  | "sales_order_created"
  | "sales_order_updated"
  | "sales_order_deleted"
  | "sales_order_confirmed"
  | "sales_order_cancelled"
  | "dispatch_created"
  | "dispatch_updated"
  | "dispatch_deleted"
  | "dispatch_processed"
  | "purchase_order_created"
  | "purchase_order_updated"
  | "purchase_order_deleted"
  | "purchase_order_confirmed"
  | "purchase_order_cancelled"
  | "grn_created"
  | "grn_updated"
  | "grn_deleted"
  | "grn_received"
  | "tenant_accessed"
  | "tenant_deactivated"
  | "tenant_reactivated"
  | "tenant_limit_overridden"
  | "impersonation_started"
  | "impersonation_ended"
  | "tenant_export"

export interface AuditEntry {
  id: number
  tenant: number
  action: AuditAction
  action_display: string
  event_scope?: "operational" | "platform"
  summary?: string
  product: number | null
  product_sku: string | null
  product_name: string | null
  user: number | null
  username: string | null
  timestamp: string
  ip_address: string | null
  details: Record<string, unknown>
}

export interface AuditListParams {
  page?: number
  page_size?: number
  ordering?: string
  action?: string
  product?: string
  user?: string
  date_from?: string
  date_to?: string
}
