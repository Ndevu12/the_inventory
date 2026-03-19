"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  bulkApi,
  fetchProducts,
  fetchLocations,
  type BulkTransferPayload,
  type BulkAdjustmentPayload,
  type BulkRevaluePayload,
} from "../api/bulk-api";
import { movementKeys } from "../../inventory/hooks/use-movements";

export function useBulkProducts() {
  return useQuery({
    queryKey: ["products", "list-all"],
    queryFn: fetchProducts,
    staleTime: 5 * 60 * 1000,
  });
}

export function useBulkLocations() {
  return useQuery({
    queryKey: ["locations", "list-all"],
    queryFn: fetchLocations,
    staleTime: 5 * 60 * 1000,
  });
}

export function useBulkTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BulkTransferPayload) => bulkApi.transfer(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: movementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stock-records"] });
    },
  });
}

export function useBulkAdjustment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BulkAdjustmentPayload) => bulkApi.adjust(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: movementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stock-records"] });
    },
  });
}

export function useBulkRevalue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BulkRevaluePayload) => bulkApi.revalue(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
}
