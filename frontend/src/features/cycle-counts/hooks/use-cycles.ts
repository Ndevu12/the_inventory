import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchCycles,
  fetchCycle,
  startCycle,
  recordCount,
  completeCycle,
  reconcileCycle,
} from "../api/cycles-api";
import type {
  CycleListParams,
  CycleCreatePayload,
  RecordCountPayload,
  ReconcilePayload,
} from "../types/cycle-count.types";

const CYCLES_KEY = "cycle-counts";

export function useCycles(params: CycleListParams = {}) {
  return useQuery({
    queryKey: [CYCLES_KEY, params],
    queryFn: () => fetchCycles(params),
  });
}

export function useCycle(id: number) {
  return useQuery({
    queryKey: [CYCLES_KEY, id],
    queryFn: () => fetchCycle(id),
    enabled: id > 0,
  });
}

export function useStartCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CycleCreatePayload) => startCycle(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY] });
    },
  });
}

export function useRecordCount(cycleId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecordCountPayload) =>
      recordCount(cycleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY, cycleId] });
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY] });
    },
  });
}

export function useCompleteCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (cycleId: number) => completeCycle(cycleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY] });
    },
  });
}

export function useReconcileCycle(cycleId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReconcilePayload) =>
      reconcileCycle(cycleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY, cycleId] });
      queryClient.invalidateQueries({ queryKey: [CYCLES_KEY] });
    },
  });
}
