import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { customersApi } from "../api/customers-api"
import type {
  CustomerListParams,
  CustomerCreatePayload,
  CustomerUpdatePayload,
} from "../types/sales.types"

const CUSTOMERS_KEY = ["customers"] as const

export function useCustomers(params?: CustomerListParams) {
  return useQuery({
    queryKey: [...CUSTOMERS_KEY, params],
    queryFn: () => customersApi.list(params as Record<string, string>),
  })
}

export function useCustomer(id: number) {
  return useQuery({
    queryKey: [...CUSTOMERS_KEY, id],
    queryFn: () => customersApi.get(id),
    enabled: id > 0,
  })
}

export function useCreateCustomer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CustomerCreatePayload) =>
      customersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CUSTOMERS_KEY })
    },
  })
}

export function useUpdateCustomer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CustomerUpdatePayload }) =>
      customersApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CUSTOMERS_KEY })
    },
  })
}

export function useDeleteCustomer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => customersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CUSTOMERS_KEY })
    },
  })
}
