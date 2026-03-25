import { useQuery } from "@tanstack/react-query";
import { warehousesApi } from "../api/warehouses-api";

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
