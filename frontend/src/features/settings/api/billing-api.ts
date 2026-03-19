import { useAuthStore } from "@/lib/auth-store"
import { apiClient } from "@/lib/api-client"
import type { BillingTenant, BillingTenantUpdatePayload } from "../types/settings.types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1"
const BILLING_BASE = "/platform/billing/tenants"

/** Trigger tenant data export (ZIP download). Platform superuser only. */
export async function exportTenantData(
  tenantId: number,
  params?: { entity_types?: string; date_from?: string; date_to?: string },
): Promise<void> {
  const url = new URL(`${API_BASE}/platform/tenants/${tenantId}/export/`, window.location.origin)
  if (params?.entity_types) url.searchParams.set("entity_types", params.entity_types)
  if (params?.date_from) url.searchParams.set("date_from", params.date_from)
  if (params?.date_to) url.searchParams.set("date_to", params.date_to)

  const { accessToken } = useAuthStore.getState()
  const headers: HeadersInit = {}
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`

  const res = await fetch(url.toString(), { headers })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)

  const blob = await res.blob()
  const disposition = res.headers.get("Content-Disposition")
  const filename =
    disposition?.match(/filename="?(.+?)"?$/)?.[1] ?? `tenant-export-${tenantId}.zip`

  const a = document.createElement("a")
  a.href = URL.createObjectURL(blob)
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}

export const billingApi = {
  list() {
    return apiClient.get<BillingTenant[]>(`${BILLING_BASE}/`)
  },

  get(id: number) {
    return apiClient.get<BillingTenant>(`${BILLING_BASE}/${id}/`)
  },

  update(id: number, payload: BillingTenantUpdatePayload) {
    return apiClient.patch<BillingTenant>(`${BILLING_BASE}/${id}/`, payload)
  },

  suspend(id: number) {
    return apiClient.post<BillingTenant>(`${BILLING_BASE}/${id}/suspend/`, {})
  },

  reactivate(id: number) {
    return apiClient.post<BillingTenant>(`${BILLING_BASE}/${id}/reactivate/`, {})
  },
}
