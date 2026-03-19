import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import {
  salesOrdersApi,
  fetchProducts,
  fetchCustomers,
} from "../api/sales-orders-api"
import type {
  SalesOrderListParams,
  SalesOrderCreatePayload,
  SalesOrderUpdatePayload,
} from "../types/sales.types"

const SO_KEY = ["sales-orders"] as const

export function useSalesOrders(params?: SalesOrderListParams) {
  return useQuery({
    queryKey: [...SO_KEY, params],
    queryFn: () => salesOrdersApi.list(params),
  })
}

export function useSalesOrder(id: number) {
  return useQuery({
    queryKey: [...SO_KEY, id],
    queryFn: () => salesOrdersApi.get(id),
    enabled: id > 0,
  })
}

export function useCreateSalesOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SalesOrderCreatePayload) =>
      salesOrdersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SO_KEY })
    },
  })
}

export function useUpdateSalesOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SalesOrderUpdatePayload }) =>
      salesOrdersApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SO_KEY })
    },
  })
}

export function useDeleteSalesOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => salesOrdersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SO_KEY })
    },
  })
}

export function useConfirmSalesOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => salesOrdersApi.confirm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SO_KEY })
    },
  })
}

export function useCancelSalesOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => salesOrdersApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SO_KEY })
    },
  })
}

export function useAllSalesOrders() {
  return useQuery({
    queryKey: [...SO_KEY, "all"],
    queryFn: () => salesOrdersApi.list({ page_size: 1000 }),
    select: (data) => data.results,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSOProducts() {
  return useQuery({
    queryKey: ["products", "list-all"],
    queryFn: fetchProducts,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSOCustomers() {
  return useQuery({
    queryKey: ["customers", "list-all-active"],
    queryFn: fetchCustomers,
    staleTime: 5 * 60 * 1000,
  })
}
