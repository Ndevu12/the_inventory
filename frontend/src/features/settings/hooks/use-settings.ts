import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { settingsApi } from "../api/settings-api"
import type { TenantUpdatePayload } from "../types/settings.types"

const TENANT_KEY = ["tenant", "current"] as const

export function useTenant() {
  return useQuery({
    queryKey: [...TENANT_KEY],
    queryFn: () => settingsApi.getCurrentTenant(),
  })
}

export function useUpdateTenant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: TenantUpdatePayload) =>
      settingsApi.updateTenant(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TENANT_KEY })
    },
  })
}
