import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { fetchLots } from "../api/lots-api";
import type { LotListParams } from "../types/lot.types";

export const lotKeys = {
  all: ["lots"] as const,
  lists: () => [...lotKeys.all, "list"] as const,
  list: (params: LotListParams) => [...lotKeys.lists(), params] as const,
  details: () => [...lotKeys.all, "detail"] as const,
  detail: (id: number) => [...lotKeys.details(), id] as const,
};

export function useLots(params: LotListParams = {}) {
  return useQuery({
    queryKey: lotKeys.list(params),
    queryFn: () => fetchLots(params),
    placeholderData: keepPreviousData,
  });
}
