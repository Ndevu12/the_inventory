import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { suppliersApi } from "../api/suppliers-api"
import type {
  SupplierListParams,
  SupplierCreatePayload,
  SupplierUpdatePayload,
} from "../types/procurement.types"

const SUPPLIERS_KEY = ["suppliers"] as const

export function useSuppliers(params?: SupplierListParams) {
  return useQuery({
    queryKey: [...SUPPLIERS_KEY, params],
    queryFn: () => suppliersApi.list(params),
  })
}

export function useActiveSuppliers() {
  return useQuery({
    queryKey: [...SUPPLIERS_KEY, "active"],
    queryFn: () => suppliersApi.list({ page_size: 1000, is_active: "true" }),
    select: (data) => data.results,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSupplier(id: number) {
  return useQuery({
    queryKey: [...SUPPLIERS_KEY, id],
    queryFn: () => suppliersApi.get(id),
    enabled: id > 0,
  })
}

export function useCreateSupplier() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SupplierCreatePayload) =>
      suppliersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY })
    },
  })
}

export function useUpdateSupplier() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SupplierUpdatePayload }) =>
      suppliersApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY })
    },
  })
}

export function useDeleteSupplier() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => suppliersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY })
    },
  })
}
