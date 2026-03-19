import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { billingApi } from "../api/billing-api"
import type { BillingTenantUpdatePayload } from "../types/settings.types"

const BILLING_KEY = ["platform-billing-tenants"] as const

export function useBillingTenants() {
  return useQuery({
    queryKey: BILLING_KEY,
    queryFn: () => billingApi.list(),
  })
}

export function useBillingTenant(id: number) {
  return useQuery({
    queryKey: [...BILLING_KEY, id],
    queryFn: () => billingApi.get(id),
    enabled: id > 0,
  })
}

export function useUpdateBillingTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: { id: number; payload: BillingTenantUpdatePayload }) =>
      billingApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BILLING_KEY })
    },
  })
}

export function useSuspendBillingTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => billingApi.suspend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BILLING_KEY })
    },
  })
}

export function useReactivateBillingTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => billingApi.reactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BILLING_KEY })
    },
  })
}
