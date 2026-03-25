import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { warehousesApi } from "../api/warehouses-api";
import type { WarehouseFormData } from "../types/warehouse.types";

const WAREHOUSES_KEY = ["warehouses"] as const;

/** Active facilities for selects and filters (paginated API; one page is enough for typical tenants). */
export function useWarehousesForSelect() {
  return useQuery({
    queryKey: [...WAREHOUSES_KEY, "select", "active"] as const,
    queryFn: () =>
      warehousesApi.list({ is_active: "true", page_size: "500", ordering: "name" }),
    select: (data) => data.results.filter((w) => w.is_active),
    staleTime: 5 * 60 * 1000,
  });
}

/** Per-facility KPIs for the locations page strip; disabled when tenant has no facilities. */
export function useWarehouseQuickStats(enabled: boolean) {
  return useQuery({
    queryKey: [...WAREHOUSES_KEY, "quick-stats"] as const,
    queryFn: () => warehousesApi.quickStats(),
    enabled,
    staleTime: 2 * 60 * 1000,
  });
}

/** Facilities listing for the warehouse admin page (search uses API ``search``). */
export function useWarehousesList(search?: string) {
  return useQuery({
    queryKey: [...WAREHOUSES_KEY, "admin-list", search ?? ""] as const,
    queryFn: () =>
      warehousesApi.list({
        page_size: "100",
        ordering: "name",
        ...(search?.trim() ? { search: search.trim() } : {}),
      }),
    select: (data) => data.results,
    staleTime: 60 * 1000,
  });
}

export function useCreateWarehouse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WarehouseFormData) => warehousesApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: WAREHOUSES_KEY });
    },
  });
}

export function useUpdateWarehouse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: Partial<WarehouseFormData>;
    }) => warehousesApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: WAREHOUSES_KEY });
    },
  });
}

export function useDeleteWarehouse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => warehousesApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: WAREHOUSES_KEY });
    },
  });
}
