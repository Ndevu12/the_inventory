import type { FacetedFilterOption } from "@/components/data-table"
import type { AuditAction } from "../types/audit.types"

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
  "tenant_accessed",
  "tenant_export",
] as const

export function getAuditActionFilterOptions(
  labelFor: (action: AuditAction) => string,
): FacetedFilterOption[] {
  return AUDIT_ACTION_VALUES.map((value) => ({
    label: labelFor(value),
    value,
  }))
}

export const AUDIT_ACTION_COLOR_MAP: Record<
  AuditAction,
  { bg: string; text: string }
> = {
  stock_received: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-800 dark:text-green-300",
  },
  stock_issued: {
    bg: "bg-orange-100 dark:bg-orange-900/30",
    text: "text-orange-800 dark:text-orange-300",
  },
  stock_transferred: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-800 dark:text-blue-300",
  },
  stock_adjusted: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-800 dark:text-yellow-300",
  },
  reservation_created: {
    bg: "bg-indigo-100 dark:bg-indigo-900/30",
    text: "text-indigo-800 dark:text-indigo-300",
  },
  reservation_fulfilled: {
    bg: "bg-emerald-100 dark:bg-emerald-900/30",
    text: "text-emerald-800 dark:text-emerald-300",
  },
  reservation_cancelled: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-800 dark:text-red-300",
  },
  cycle_count_started: {
    bg: "bg-cyan-100 dark:bg-cyan-900/30",
    text: "text-cyan-800 dark:text-cyan-300",
  },
  cycle_count_reconciled: {
    bg: "bg-teal-100 dark:bg-teal-900/30",
    text: "text-teal-800 dark:text-teal-300",
  },
  bulk_operation: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-800 dark:text-purple-300",
  },
  tenant_accessed: {
    bg: "bg-gray-100 dark:bg-gray-800/30",
    text: "text-gray-800 dark:text-gray-300",
  },
  tenant_export: {
    bg: "bg-violet-100 dark:bg-violet-900/30",
    text: "text-violet-800 dark:text-violet-300",
  },
}
