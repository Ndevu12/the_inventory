import type { FacetedFilterOption } from "@/components/data-table"
import type { AuditAction, AuditEntry } from "../types/audit.types"

/** Stable order for audit action faceted filters (labels from i18n `Audit.actionLabels`). */
export const AUDIT_ACTION_VALUES: readonly AuditAction[] = [
  "stock_received",
  "stock_issued",
  "stock_transferred",
  "stock_adjusted",
  "reservation_created",
  "reservation_fulfilled",
  "reservation_cancelled",
  "cycle_count_started",
  "cycle_count_reconciled",
  "bulk_operation",
  "product_created",
  "product_updated",
  "product_deleted",
  "category_created",
  "category_updated",
  "category_deleted",
  "warehouse_created",
  "warehouse_updated",
  "warehouse_deleted",
  "location_created",
  "location_updated",
  "location_deleted",
  "customer_created",
  "customer_updated",
  "customer_deleted",
  "supplier_created",
  "supplier_updated",
  "supplier_deleted",
  "sales_order_created",
  "sales_order_updated",
  "sales_order_deleted",
  "sales_order_confirmed",
  "sales_order_cancelled",
  "dispatch_created",
  "dispatch_updated",
  "dispatch_deleted",
  "dispatch_processed",
  "purchase_order_created",
  "purchase_order_updated",
  "purchase_order_deleted",
  "purchase_order_confirmed",
  "purchase_order_cancelled",
  "grn_created",
  "grn_updated",
  "grn_deleted",
  "grn_received",
  "tenant_accessed",
  "tenant_deactivated",
  "tenant_reactivated",
  "tenant_limit_overridden",
  "impersonation_started",
  "impersonation_ended",
  "tenant_export",
] as const

const AUDIT_ACTION_VALUE_SET = new Set<string>(AUDIT_ACTION_VALUES)

/** Whether ``value`` is a known backend audit action. */
export function isAuditAction(value: string): value is AuditAction {
  return AUDIT_ACTION_VALUE_SET.has(value)
}

/** Localized action label with server fallback for forward-compatible enum values. */
export function getAuditActionLabel(
  entry: AuditEntry,
  labelForKnown: (action: AuditAction) => string,
): string {
  if (isAuditAction(entry.action)) return labelForKnown(entry.action)
  const serverLabel = entry.action_display?.trim()
  if (serverLabel) return serverLabel
  return String(entry.action)
}

export function getAuditActionFilterOptions(
  labelFor: (action: AuditAction) => string,
): FacetedFilterOption[] {
  return AUDIT_ACTION_VALUES.map((value) => ({
    label: labelFor(value),
    value,
  }))
}

const _c = {
  green: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-800 dark:text-green-300",
  },
  orange: {
    bg: "bg-orange-100 dark:bg-orange-900/30",
    text: "text-orange-800 dark:text-orange-300",
  },
  blue: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-800 dark:text-blue-300",
  },
  yellow: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-800 dark:text-yellow-300",
  },
  red: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-800 dark:text-red-300",
  },
  indigo: {
    bg: "bg-indigo-100 dark:bg-indigo-900/30",
    text: "text-indigo-800 dark:text-indigo-300",
  },
  emerald: {
    bg: "bg-emerald-100 dark:bg-emerald-900/30",
    text: "text-emerald-800 dark:text-emerald-300",
  },
  cyan: {
    bg: "bg-cyan-100 dark:bg-cyan-900/30",
    text: "text-cyan-800 dark:text-cyan-300",
  },
  teal: {
    bg: "bg-teal-100 dark:bg-teal-900/30",
    text: "text-teal-800 dark:text-teal-300",
  },
  purple: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-800 dark:text-purple-300",
  },
  slate: {
    bg: "bg-slate-100 dark:bg-slate-800/40",
    text: "text-slate-800 dark:text-slate-300",
  },
  sky: {
    bg: "bg-sky-100 dark:bg-sky-900/30",
    text: "text-sky-800 dark:text-sky-300",
  },
  violet: {
    bg: "bg-violet-100 dark:bg-violet-900/30",
    text: "text-violet-800 dark:text-violet-300",
  },
  pink: {
    bg: "bg-pink-100 dark:bg-pink-900/30",
    text: "text-pink-800 dark:text-pink-300",
  },
  amber: {
    bg: "bg-amber-100 dark:bg-amber-900/30",
    text: "text-amber-800 dark:text-amber-300",
  },
  rose: {
    bg: "bg-rose-100 dark:bg-rose-900/30",
    text: "text-rose-800 dark:text-rose-300",
  },
  fuchsia: {
    bg: "bg-fuchsia-100 dark:bg-fuchsia-900/30",
    text: "text-fuchsia-800 dark:text-fuchsia-300",
  },
  stone: {
    bg: "bg-stone-100 dark:bg-stone-800/40",
    text: "text-stone-800 dark:text-stone-300",
  },
} as const

export const AUDIT_ACTION_COLOR_MAP: Record<
  AuditAction,
  { bg: string; text: string }
> = {
  stock_received: _c.green,
  stock_issued: _c.orange,
  stock_transferred: _c.blue,
  stock_adjusted: _c.yellow,
  reservation_created: _c.indigo,
  reservation_fulfilled: _c.emerald,
  reservation_cancelled: _c.red,
  cycle_count_started: _c.cyan,
  cycle_count_reconciled: _c.teal,
  bulk_operation: _c.purple,
  product_created: _c.sky,
  product_updated: _c.blue,
  product_deleted: _c.red,
  category_created: _c.sky,
  category_updated: _c.blue,
  category_deleted: _c.red,
  warehouse_created: _c.violet,
  warehouse_updated: _c.blue,
  warehouse_deleted: _c.red,
  location_created: _c.teal,
  location_updated: _c.blue,
  location_deleted: _c.red,
  customer_created: _c.pink,
  customer_updated: _c.blue,
  customer_deleted: _c.red,
  supplier_created: _c.amber,
  supplier_updated: _c.blue,
  supplier_deleted: _c.red,
  sales_order_created: _c.rose,
  sales_order_updated: _c.blue,
  sales_order_deleted: _c.red,
  sales_order_confirmed: _c.emerald,
  sales_order_cancelled: _c.orange,
  dispatch_created: _c.fuchsia,
  dispatch_updated: _c.blue,
  dispatch_deleted: _c.red,
  dispatch_processed: _c.teal,
  purchase_order_created: _c.amber,
  purchase_order_updated: _c.blue,
  purchase_order_deleted: _c.red,
  purchase_order_confirmed: _c.emerald,
  purchase_order_cancelled: _c.orange,
  grn_created: _c.stone,
  grn_updated: _c.blue,
  grn_deleted: _c.red,
  grn_received: _c.green,
  tenant_accessed: _c.slate,
  tenant_deactivated: _c.red,
  tenant_reactivated: _c.emerald,
  tenant_limit_overridden: _c.amber,
  impersonation_started: _c.violet,
  impersonation_ended: _c.slate,
  tenant_export: _c.violet,
}
