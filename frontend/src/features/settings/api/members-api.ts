import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types"
import type {
  TenantMember,
  MemberUpdatePayload,
  MemberListParams,
} from "../types/settings.types"

const BASE = "/tenants/members"

function toQueryParams(
  params?: MemberListParams
): Record<string, string> | undefined {
  if (!params) return undefined
  const out: Record<string, string> = {}
  if (params.page != null) out.page = String(params.page)
  if (params.page_size != null) out.page_size = String(params.page_size)
  if (params.search) out.search = params.search
  if (params.ordering) out.ordering = params.ordering
  if (params.role) out.role = params.role
  return Object.keys(out).length > 0 ? out : undefined
}

export const membersApi = {
  list(params?: MemberListParams) {
    return apiClient.get<PaginatedResponse<TenantMember>>(
      `${BASE}/`,
      toQueryParams(params)
    )
  },

  get(id: number) {
    return apiClient.get<TenantMember>(`${BASE}/${id}/`)
  },

  update(id: number, payload: MemberUpdatePayload) {
    return apiClient.patch<TenantMember>(`${BASE}/${id}/`, payload)
  },

  remove(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },
}
