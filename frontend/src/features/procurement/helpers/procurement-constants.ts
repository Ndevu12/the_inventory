import type { PaymentTerms, PurchaseOrderStatus } from "../types/procurement.types"

export const PAYMENT_TERMS_VALUES = [
  "net_30",
  "net_60",
  "net_90",
  "cod",
  "prepaid",
] as const satisfies readonly PaymentTerms[]

/** Human-readable label for a stored payment_terms code (API value). */
export function paymentTermsLabel(
  code: string | null | undefined,
  t: (key: string) => string,
): string {
  if (code == null || code === "") return ""
  const trimmed = code.trim() as PaymentTerms
  if ((PAYMENT_TERMS_VALUES as readonly string[]).includes(trimmed)) {
    return t(trimmed)
  }
  return code
}

// ─── Purchase Order Statuses ────────────────────────────────────────────────

export const PO_STATUS_VALUES = [
  "draft",
  "confirmed",
  "received",
  "cancelled",
] as const satisfies readonly PurchaseOrderStatus[]

export const PO_STATUS_COLOR_MAP: Record<
  PurchaseOrderStatus,
  { bg: string; text: string }
> = {
  draft: { bg: "bg-gray-100 dark:bg-gray-800/30", text: "text-gray-800 dark:text-gray-300" },
  confirmed: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-800 dark:text-blue-300" },
  received: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
  cancelled: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-300" },
}
