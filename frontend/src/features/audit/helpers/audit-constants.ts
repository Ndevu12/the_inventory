import type { FacetedFilterOption } from "@/components/data-table"
import type { AuditAction } from "../types/audit.types"

export const AUDIT_ACTION_OPTIONS: FacetedFilterOption[] = [
  { label: "Stock Received", value: "stock_received" },
  { label: "Stock Issued", value: "stock_issued" },
  { label: "Stock Transferred", value: "stock_transferred" },
  { label: "Stock Adjusted", value: "stock_adjusted" },
  { label: "Reservation Created", value: "reservation_created" },
  { label: "Reservation Fulfilled", value: "reservation_fulfilled" },
  { label: "Reservation Cancelled", value: "reservation_cancelled" },
  { label: "Cycle Count Started", value: "cycle_count_started" },
  { label: "Cycle Count Reconciled", value: "cycle_count_reconciled" },
  { label: "Bulk Operation", value: "bulk_operation" },
  { label: "Tenant Accessed", value: "tenant_accessed" },
  { label: "Tenant Data Exported", value: "tenant_export" },
]

export const AUDIT_ACTION_MAP: Record<AuditAction, string> = {
  stock_received: "Stock Received",
  stock_issued: "Stock Issued",
  stock_transferred: "Stock Transferred",
  stock_adjusted: "Stock Adjusted",
  reservation_created: "Reservation Created",
  reservation_fulfilled: "Reservation Fulfilled",
  reservation_cancelled: "Reservation Cancelled",
  cycle_count_started: "Cycle Count Started",
  cycle_count_reconciled: "Cycle Count Reconciled",
  bulk_operation: "Bulk Operation",
  tenant_accessed: "Tenant Accessed",
  tenant_export: "Tenant Data Exported",
}

export const AUDIT_ACTION_COLOR_MAP: Record<
  AuditAction,
  { bg: string; text: string }
> = {
  stock_received: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
  stock_issued: { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-800 dark:text-orange-300" },
  stock_transferred: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-800 dark:text-blue-300" },
  stock_adjusted: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-800 dark:text-yellow-300" },
  reservation_created: { bg: "bg-indigo-100 dark:bg-indigo-900/30", text: "text-indigo-800 dark:text-indigo-300" },
  reservation_fulfilled: { bg: "bg-emerald-100 dark:bg-emerald-900/30", text: "text-emerald-800 dark:text-emerald-300" },
  reservation_cancelled: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-300" },
  cycle_count_started: { bg: "bg-cyan-100 dark:bg-cyan-900/30", text: "text-cyan-800 dark:text-cyan-300" },
  cycle_count_reconciled: { bg: "bg-teal-100 dark:bg-teal-900/30", text: "text-teal-800 dark:text-teal-300" },
  bulk_operation: { bg: "bg-purple-100 dark:bg-purple-900/30", text: "text-purple-800 dark:text-purple-300" },
  tenant_accessed: { bg: "bg-gray-100 dark:bg-gray-800/30", text: "text-gray-800 dark:text-gray-300" },
  tenant_export: { bg: "bg-violet-100 dark:bg-violet-900/30", text: "text-violet-800 dark:text-violet-300" },
}
