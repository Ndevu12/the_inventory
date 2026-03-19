import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  AuditEntry,
  AuditListParams,
  PlatformAuditEntry,
  PlatformAuditListParams,
} from "../types/audit.types"

const BASE = "/audit-log"
const PLATFORM_BASE = "/platform/audit-log"

function toQueryParams(
  params: AuditListParams,
): Record<string, string> | undefined {
  const query: Record<string, string> = {}
  if (params.page) query.page = String(params.page)
  if (params.page_size) query.page_size = String(params.page_size)
  if (params.ordering) query.ordering = params.ordering
  if (params.action) query.action = params.action
  if (params.product) query.product = params.product
  if (params.user) query.user = params.user
  if (params.date_from) query.date_from = params.date_from
  if (params.date_to) query.date_to = params.date_to
  return Object.keys(query).length > 0 ? query : undefined
}

function toPlatformQueryParams(
  params: PlatformAuditListParams,
): Record<string, string> | undefined {
  const query: Record<string, string> = {}
  if (params.page) query.page = String(params.page)
  if (params.page_size) query.page_size = String(params.page_size)
  if (params.ordering) query.ordering = params.ordering ?? "-timestamp"
  if (params.action) query.action = params.action
  if (params.product) query.product = params.product
  if (params.user) query.user = params.user
  if (params.tenant) query.tenant = params.tenant
  if (params.date_from) query.date_from = params.date_from
  if (params.date_to) query.date_to = params.date_to
  return Object.keys(query).length > 0 ? query : undefined
}

export function fetchAuditLog(
  params: AuditListParams = {},
): Promise<PaginatedResponse<AuditEntry>> {
  return apiClient.get<PaginatedResponse<AuditEntry>>(
    `${BASE}/`,
    toQueryParams(params),
  )
}

export function fetchAuditEntry(id: number): Promise<AuditEntry> {
  return apiClient.get<AuditEntry>(`${BASE}/${id}/`)
}

export function exportAuditCsv(
  params: AuditListParams = {},
): string {
  const qp = toQueryParams(params)
  const searchParams = qp ? new URLSearchParams(qp) : new URLSearchParams()
  searchParams.set("export", "csv")
  return `${BASE}/export/?${searchParams.toString()}`
}

// Platform audit (superuser only)
export function fetchPlatformAuditLog(
  params: PlatformAuditListParams = {},
): Promise<PaginatedResponse<PlatformAuditEntry>> {
  return apiClient.get<PaginatedResponse<PlatformAuditEntry>>(
    `${PLATFORM_BASE}/`,
    toPlatformQueryParams(params),
  )
}

/** Trigger authenticated platform audit export (CSV or Excel). */
export async function triggerPlatformAuditExport(
  format: "csv" | "xlsx",
  params: PlatformAuditListParams = {},
): Promise<void> {
  const qp = toPlatformQueryParams(params)
  const searchParams = qp ? new URLSearchParams(qp) : new URLSearchParams()
  searchParams.set("format", format)
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1"
  const url = `${apiBase}${PLATFORM_BASE}/export/?${searchParams.toString()}`

  const { accessToken, tenantSlug } = await import("@/lib/auth-store").then(
    (m) => m.useAuthStore.getState(),
  )
  const headers: HeadersInit = {}
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`
  if (tenantSlug) headers["X-Tenant"] = tenantSlug

  const res = await fetch(url, { headers })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)

  const blob = await res.blob()
  const disposition = res.headers.get("Content-Disposition")
  const filename =
    disposition?.match(/filename="?(.+?)"?$/)?.[1] ??
    `platform_audit_log.${format}`

  const a = document.createElement("a")
  a.href = URL.createObjectURL(blob)
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}
