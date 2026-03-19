import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { purchaseOrdersApi } from "../api/purchase-orders-api"
import type {
  PurchaseOrderListParams,
  PurchaseOrderCreatePayload,
  PurchaseOrderUpdatePayload,
} from "../types/procurement.types"

const PO_KEY = ["purchase-orders"] as const

export function usePurchaseOrders(params?: PurchaseOrderListParams) {
  return useQuery({
    queryKey: [...PO_KEY, params],
    queryFn: () => purchaseOrdersApi.list(params),
  })
}

export function usePurchaseOrder(id: number) {
  return useQuery({
    queryKey: [...PO_KEY, id],
    queryFn: () => purchaseOrdersApi.get(id),
    enabled: id > 0,
  })
}

export function useCreatePurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: PurchaseOrderCreatePayload) =>
      purchaseOrdersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PO_KEY })
    },
  })
}

export function useUpdatePurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: PurchaseOrderUpdatePayload }) =>
      purchaseOrdersApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PO_KEY })
    },
  })
}

export function useDeletePurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseOrdersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PO_KEY })
    },
  })
}

export function useConfirmPurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseOrdersApi.confirm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PO_KEY })
    },
  })
}

export function useCancelPurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseOrdersApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PO_KEY })
    },
  })
}
