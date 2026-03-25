"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import { useMemo } from "react";
import type { PaginatedResponse } from "@/types/api-common";
import { locationsApi } from "../api/locations-api";
import type {
  StockLocation,
  StockLocationFormData,
} from "../types/location.types";

const LOCATIONS_KEY = ["stock-locations"] as const;

/** DRF ``StandardPagination`` max ``page_size`` is 100. */
export const LOCATIONS_PAGE_SIZE = "100";

/** Rows loaded when expanding a location in the tree (capped preview). */
export const LOCATION_STOCK_PREVIEW_PAGE_SIZE = "15";

/** Page size inside the “view all” sheet (under API max). */
export const LOCATION_STOCK_DRAWER_PAGE_SIZE = "50";

function getNextDrfPage(
  lastPage: PaginatedResponse<unknown>,
): number | undefined {
  if (!lastPage.next) return undefined;
  try {
    const base =
      typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost";
    const url = lastPage.next.startsWith("http")
      ? new URL(lastPage.next)
      : new URL(lastPage.next, base);
    const page = url.searchParams.get("page");
    if (page) return parseInt(page, 10);
    return undefined;
  } catch {
    return undefined;
  }
}

async function fetchAllLocationsPages(): Promise<StockLocation[]> {
  const all: StockLocation[] = [];
  let page = 1;
  const listParams = { page_size: LOCATIONS_PAGE_SIZE };
  for (;;) {
    const data = await locationsApi.list({
      ...listParams,
      page: String(page),
    });
    all.push(...data.results);
    const next = getNextDrfPage(data);
    if (next === undefined) break;
    page = next;
  }
  return all;
}

export function useLocations(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, params],
    queryFn: () => locationsApi.list(params),
  });
}

/**
 * Paginated locations for the location list UI (infinite scroll).
 * Uses ``page_size`` at the API maximum instead of a single oversized page.
 */
export function useInfiniteLocations(params?: Record<string, string>) {
  const listParams = useMemo(
    () => ({
      page_size: LOCATIONS_PAGE_SIZE,
      ...(params ?? {}),
    }),
    [params],
  );

  return useInfiniteQuery({
    queryKey: [...LOCATIONS_KEY, "infinite", listParams],
    queryFn: ({ pageParam }) =>
      locationsApi.list({ ...listParams, page: String(pageParam) }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => getNextDrfPage(lastPage),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * All locations for forms (e.g. reservation create). Fetches every page
 * with the standard page size until exhausted — no ``page_size: 1000``.
 */
export function useAllLocations(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, "all-paged", LOCATIONS_PAGE_SIZE],
    queryFn: fetchAllLocationsPages,
    staleTime: 5 * 60 * 1000,
    enabled: options?.enabled ?? true,
  });
}

export function useLocation(id: number) {
  return useQuery({
    queryKey: [...LOCATIONS_KEY, id],
    queryFn: () => locationsApi.get(id),
    enabled: id > 0,
  });
}

/** Merged rows for deep-link / jump-to (``id__in``). */
export function useLocationsByIds(ids: number[]) {
  const sortedKey = [...ids].sort((a, b) => a - b).join(",");
  return useQuery({
    queryKey: [...LOCATIONS_KEY, "by-ids", sortedKey],
    queryFn: () =>
      locationsApi.list({
        id__in: sortedKey,
        page_size: LOCATIONS_PAGE_SIZE,
      }),
    enabled: ids.length > 0,
    staleTime: 60 * 1000,
  });
}

export function useLocationStockPage(
  id: number,
  params: { page: number; page_size: string },
  options?: { enabled?: boolean },
) {
  const { page, page_size } = params;
  const enabled = options?.enabled ?? true;
  return useQuery({
    queryKey: [...LOCATIONS_KEY, id, "stock", page, page_size],
    queryFn: () =>
      locationsApi.stockAt(id, {
        page: String(page),
        page_size,
      }),
    enabled: enabled && id > 0,
    staleTime: 60 * 1000,
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
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: Partial<StockLocationFormData>;
    }) => locationsApi.update(id, data),
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
