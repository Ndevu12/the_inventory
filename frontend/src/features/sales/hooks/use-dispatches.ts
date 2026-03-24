import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import {
  dispatchesApi,
  fetchSalesOrdersForDispatch,
  fetchLocations,
} from "../api/dispatches-api"
import type {
  DispatchListParams,
  DispatchCreatePayload,
  DispatchUpdatePayload,
} from "../types/dispatch.types"

const DISPATCHES_KEY = ["dispatches"] as const

export function useDispatches(params?: DispatchListParams) {
  return useQuery({
    queryKey: [...DISPATCHES_KEY, params],
    queryFn: () => dispatchesApi.list(params),
  })
}

export function useDispatch(id: number) {
  return useQuery({
    queryKey: [...DISPATCHES_KEY, id],
    queryFn: () => dispatchesApi.get(id),
    enabled: id > 0,
  })
}

export function useCreateDispatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: DispatchCreatePayload) =>
      dispatchesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DISPATCHES_KEY })
    },
  })
}

export function useUpdateDispatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number
      payload: DispatchUpdatePayload
    }) => dispatchesApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DISPATCHES_KEY })
    },
  })
}

export function useDeleteDispatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => dispatchesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DISPATCHES_KEY })
    },
  })
}

export function useProcessDispatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      issueAvailableOnly,
    }: {
      id: number
      issueAvailableOnly?: boolean
    }) =>
      dispatchesApi.process(
        id,
        issueAvailableOnly ? { issue_available_only: true } : undefined,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DISPATCHES_KEY })
      queryClient.invalidateQueries({ queryKey: ["sales-orders"] })
    },
  })
}

export function useDispatchFulfillmentPreview(
  dispatchId: number | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [...DISPATCHES_KEY, dispatchId, "fulfillment-preview"],
    queryFn: () => dispatchesApi.fulfillmentPreview(dispatchId!),
    enabled: enabled && dispatchId != null && dispatchId > 0,
  })
}

export function useDispatchSalesOrders() {
  return useQuery({
    queryKey: ["sales-orders", "for-dispatch", "confirmed"],
    queryFn: fetchSalesOrdersForDispatch,
    staleTime: 60 * 1000,
  })
}

export function useDispatchLocations() {
  return useQuery({
    queryKey: ["locations", "list-all"],
    queryFn: fetchLocations,
    staleTime: 5 * 60 * 1000,
  })
}
