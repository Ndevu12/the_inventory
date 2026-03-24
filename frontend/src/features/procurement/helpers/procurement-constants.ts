import type { PaymentTerms, PurchaseOrderStatus } from "../types/procurement.types"

export const PAYMENT_TERMS_OPTIONS: {
  value: PaymentTerms
  label: string
}[] = [
  { value: "net_30", label: "Net 30" },
  { value: "net_60", label: "Net 60" },
  { value: "net_90", label: "Net 90" },
  { value: "cod", label: "Cash on Delivery" },
  { value: "prepaid", label: "Prepaid" },
]

export const PAYMENT_TERMS_MAP: Record<PaymentTerms, string> =
  Object.fromEntries(
    PAYMENT_TERMS_OPTIONS.map((o) => [o.value, o.label])
  ) as Record<PaymentTerms, string>

/** Human-readable label for a stored payment_terms code (API value). */
export function paymentTermsLabel(code: string | null | undefined): string {
  if (code == null || code === "") return ""
  const trimmed = code.trim() as PaymentTerms
  return PAYMENT_TERMS_MAP[trimmed] ?? code
}

// ─── Purchase Order Statuses ────────────────────────────────────────────────

export const PO_STATUS_OPTIONS: {
  value: PurchaseOrderStatus
  label: string
}[] = [
  { value: "draft", label: "Draft" },
  { value: "confirmed", label: "Confirmed" },
  { value: "received", label: "Received" },
  { value: "cancelled", label: "Cancelled" },
]

export const PO_STATUS_MAP: Record<PurchaseOrderStatus, string> =
  Object.fromEntries(
    PO_STATUS_OPTIONS.map((o) => [o.value, o.label])
  ) as Record<PurchaseOrderStatus, string>

export const PO_STATUS_COLOR_MAP: Record<
  PurchaseOrderStatus,
  { bg: string; text: string }
> = {
  draft: { bg: "bg-gray-100 dark:bg-gray-800/30", text: "text-gray-800 dark:text-gray-300" },
  confirmed: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-800 dark:text-blue-300" },
  received: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
  cancelled: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-300" },
}
