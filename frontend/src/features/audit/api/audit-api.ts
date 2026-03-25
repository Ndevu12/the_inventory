import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type { AuditEntry, AuditListParams } from "../types/audit.types"

const BASE = "/audit-log"

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
