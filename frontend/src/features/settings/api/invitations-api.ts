import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api-common"
import type {
  Invitation,
  InvitationCreatePayload,
  InvitationInfo,
  AcceptInvitationPayload,
  PlatformInvitation,
  PlatformInvitationListParams,
} from "../types/settings.types"

const BASE = "/tenants/invitations"
const PLATFORM_BASE = "/platform/invitations"

function toPlatformQueryParams(
  params?: PlatformInvitationListParams
): Record<string, string> | undefined {
  if (!params) return undefined
  const query: Record<string, string> = {}
  if (params.page) query.page = String(params.page)
  if (params.page_size) query.page_size = String(params.page_size)
  if (params.ordering) query.ordering = params.ordering
  if (params.status) query.status = params.status
  if (params.tenant) query.tenant = String(params.tenant)
  if (params.date_from) query.date_from = params.date_from
  if (params.date_to) query.date_to = params.date_to
  return Object.keys(query).length > 0 ? query : undefined
}

export const invitationsApi = {
  list() {
    return apiClient.get<Invitation[]>(`${BASE}/`)
  },

  create(payload: InvitationCreatePayload) {
    return apiClient.post<Invitation>(`${BASE}/`, payload)
  },

  cancel(id: number) {
    return apiClient.delete(`${BASE}/${id}/`)
  },

  getInfo(token: string) {
    return apiClient.get<InvitationInfo>(`/auth/invitations/${token}/`)
  },

  accept(token: string, payload: AcceptInvitationPayload) {
    return apiClient.post<{
      detail: string
      access: string
      refresh: string
      user: {
        id: number
        username: string
        email: string
        first_name: string
        last_name: string
        is_staff: boolean
      }
      tenant: {
        id: number
        name: string
        slug: string
        role: string
      }
      memberships?: Array<{
        tenant__id: number
        tenant__name: string
        tenant__slug: string
        role: string
        is_default: boolean
      }>
    }>(`/auth/invitations/${token}/accept/`, payload)
  },

  // Platform admin (superuser only)
  listPlatform(params?: PlatformInvitationListParams) {
    return apiClient.get<PaginatedResponse<PlatformInvitation>>(
      `${PLATFORM_BASE}/`,
      toPlatformQueryParams(params),
    )
  },

  cancelPlatform(id: number) {
    return apiClient.delete(`${PLATFORM_BASE}/${id}/`)
  },

  resendPlatform(id: number) {
    return apiClient.post<PlatformInvitation>(
      `${PLATFORM_BASE}/${id}/resend/`,
      {},
    )
  },
}
