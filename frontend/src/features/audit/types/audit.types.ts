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
  | "tenant_accessed"
  | "tenant_export"

export interface AuditEntry {
  id: number
  tenant: number
  action: AuditAction
  action_display: string
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

/** Platform audit entry (superuser view across all tenants) */
export interface PlatformAuditEntry extends AuditEntry {
  tenant_name: string
  tenant_slug: string
  object_type: string
  object_id: string | null
}

export interface PlatformAuditListParams extends AuditListParams {
  tenant?: string
}
