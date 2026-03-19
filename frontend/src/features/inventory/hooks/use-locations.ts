import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { locationsApi } from "../api/locations-api";
import type { StockLocationFormData } from "../types/location.types";

const LOCATIONS_KEY = ["stock-locations"] as const;

export function useLocations(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, params],
    queryFn: () => locationsApi.list(params),
  });
}

export function useAllLocations() {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, "all"],
    queryFn: () => locationsApi.list({ page_size: "1000" }),
    select: (data) => data.results,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLocation(id: number) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, id],
    queryFn: () => locationsApi.get(id),
    enabled: id > 0,
  });
}

export function useLocationStock(id: number) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, id, "stock"],
    queryFn: () => locationsApi.stockAt(id),
    enabled: id > 0,
  });
}

export function useCreateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: StockLocationFormData) => locationsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: LOCATIONS_KEY }),
  });
}

export function useUpdateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<StockLocationFormData> }) =>
      locationsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: LOCATIONS_KEY }),
  });
}

export function useDeleteLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => locationsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: LOCATIONS_KEY }),
  });
}
