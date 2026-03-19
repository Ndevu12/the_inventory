import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types"
import type {
  PlatformUser,
  PlatformUserCreatePayload,
  PlatformUserUpdatePayload,
  PlatformUserListParams,
  PlatformTenant,
} from "../types/settings.types"

const USERS_BASE = "/platform/users"
const TENANTS_BASE = "/platform/tenants"

function toQueryParams(
  params?: PlatformUserListParams
): Record<string, string> | undefined {
  if (!params) return undefined
  const out: Record<string, string> = {}
  if (params.page != null) out.page = String(params.page)
  if (params.page_size != null) out.page_size = String(params.page_size)
  if (params.search) out.search = params.search
  if (params.ordering) out.ordering = params.ordering
  if (params.is_active != null) out.is_active = String(params.is_active)
  if (params.is_staff != null) out.is_staff = String(params.is_staff)
  if (params.tenant != null) out.tenant = String(params.tenant)
  return Object.keys(out).length > 0 ? out : undefined
}

export const platformUsersApi = {
  list(params?: PlatformUserListParams) {
    return apiClient.get<PaginatedResponse<PlatformUser>>(
      `${USERS_BASE}/`,
      toQueryParams(params)
    )
  },

  get(id: number) {
    return apiClient.get<PlatformUser>(`${USERS_BASE}/${id}/`)
  },

  create(payload: PlatformUserCreatePayload) {
    return apiClient.post<PlatformUser>(`${USERS_BASE}/`, payload)
  },

  update(id: number, payload: PlatformUserUpdatePayload) {
    return apiClient.patch<PlatformUser>(`${USERS_BASE}/${id}/`, payload)
  },

  remove(id: number) {
    return apiClient.delete(`${USERS_BASE}/${id}/`)
  },

  resetPassword(id: number, new_password: string) {
    return apiClient.post<{ detail: string }>(
      `${USERS_BASE}/${id}/reset_password/`,
      { new_password }
    )
  },

  assignTenant(
    userId: number,
    payload: { tenant_id: number; role?: string; is_default?: boolean }
  ) {
    return apiClient.post<PlatformUser>(
      `${USERS_BASE}/${userId}/assign-tenant/`,
      payload
    )
  },

  removeMembership(userId: number, membershipId: number) {
    return apiClient.delete(
      `${USERS_BASE}/${userId}/memberships/${membershipId}/`
    )
  },
}

export const platformTenantsApi = {
  list() {
    return apiClient.get<PlatformTenant[]>(`${TENANTS_BASE}/`)
  },
}
