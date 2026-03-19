import { apiClient } from "@/lib/api-client"
import type { Tenant, TenantUpdatePayload } from "../types/settings.types"

const BASE = "/tenants"

export const settingsApi = {
  getCurrentTenant() {
    return apiClient.get<Tenant>(`${BASE}/current/`)
  },

  updateTenant(payload: TenantUpdatePayload) {
    return apiClient.patch<Tenant>(`${BASE}/current/`, payload)
  },
}
