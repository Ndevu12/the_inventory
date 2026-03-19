import { create } from "zustand";
import { DEFAULT_PAGE_SIZE } from "@/lib/utils/constants";
import type { CycleStatus } from "../types/cycle-count.types";

interface CycleFiltersState {
  search: string;
  status: CycleStatus | "";
  page: number;
  pageSize: number;
  ordering: string;
}

interface CycleFiltersActions {
  setSearch: (search: string) => void;
  setStatus: (status: CycleStatus | "") => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setOrdering: (ordering: string) => void;
  reset: () => void;
}

const initialState: CycleFiltersState = {
  search: "",
  status: "",
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  ordering: "-scheduled_date",
};

export const useCycleFiltersStore = create<
  CycleFiltersState & CycleFiltersActions
>()((set) => ({
  ...initialState,
  setSearch: (search) => set({ search, page: 1 }),
  setStatus: (status) => set({ status, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setOrdering: (ordering) => set({ ordering }),
  reset: () => set(initialState),
}));
