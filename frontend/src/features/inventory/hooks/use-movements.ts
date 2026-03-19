"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchMovements,
  fetchMovement,
  fetchProducts,
  fetchLocations,
  createMovement,
  type MovementListParams,
  type StockMovementCreatePayload,
} from "../api/movements-api";

export const movementKeys = {
  all: ["movements"] as const,
  lists: () => [...movementKeys.all, "list"] as const,
  list: (params: MovementListParams) =>
    [...movementKeys.lists(), params] as const,
  details: () => [...movementKeys.all, "detail"] as const,
  detail: (id: number) => [...movementKeys.details(), id] as const,
};

export function useMovements(params: MovementListParams = {}) {
  return useQuery({
    queryKey: movementKeys.list(params),
    queryFn: () => fetchMovements(params),
  });
}

export function useMovement(id: number) {
  return useQuery({
    queryKey: movementKeys.detail(id),
    queryFn: () => fetchMovement(id),
    enabled: id > 0,
  });
}

export function useCreateMovement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: StockMovementCreatePayload) =>
      createMovement(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: movementKeys.lists() });
    },
  });
}

export function useProducts() {
  return useQuery({
    queryKey: ["products", "list-all"],
    queryFn: fetchProducts,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLocations() {
  return useQuery({
    queryKey: ["locations", "list-all"],
    queryFn: fetchLocations,
    staleTime: 5 * 60 * 1000,
  });
}
