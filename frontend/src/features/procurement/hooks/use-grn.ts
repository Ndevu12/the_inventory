import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { grnApi, fetchPurchaseOrders, fetchLocations } from "../api/grn-api"
import type {
  GRNListParams,
  GRNCreatePayload,
  GRNUpdatePayload,
} from "../types/grn.types"

const GRN_KEY = ["goods-received-notes"] as const

export function useGRNs(params?: GRNListParams) {
  return useQuery({
    queryKey: [...GRN_KEY, params],
    queryFn: () => grnApi.list(params),
  })
}

export function useGRN(id: number) {
  return useQuery({
    queryKey: [...GRN_KEY, id],
    queryFn: () => grnApi.get(id),
    enabled: id > 0,
  })
}

export function useCreateGRN() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: GRNCreatePayload) => grnApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GRN_KEY })
    },
  })
}

export function useUpdateGRN() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GRNUpdatePayload }) =>
      grnApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GRN_KEY })
    },
  })
}

export function useDeleteGRN() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => grnApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GRN_KEY })
    },
  })
}

export function useReceiveGRN() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => grnApi.receive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GRN_KEY })
    },
  })
}

export function usePurchaseOrders() {
  return useQuery({
    queryKey: ["purchase-orders", "list-all"],
    queryFn: fetchPurchaseOrders,
    staleTime: 5 * 60 * 1000,
  })
}

export function useGRNLocations() {
  return useQuery({
    queryKey: ["locations", "list-all"],
    queryFn: fetchLocations,
    staleTime: 5 * 60 * 1000,
  })
}
