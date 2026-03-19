import { create } from "zustand";
import type { ReservationStatus } from "../types/reservation.types";

interface ReservationFiltersState {
  search: string;
  status: ReservationStatus | "";
  page: number;
  pageSize: number;
  ordering: string;
}

interface ReservationFiltersActions {
  setSearch: (search: string) => void;
  setStatus: (status: ReservationStatus | "") => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setOrdering: (ordering: string) => void;
  reset: () => void;
}

const initialState: ReservationFiltersState = {
  search: "",
  status: "",
  page: 1,
  pageSize: 10,
  ordering: "-created_at",
};

export const useReservationFiltersStore = create<
  ReservationFiltersState & ReservationFiltersActions
>()((set) => ({
  ...initialState,
  setSearch: (search) => set({ search, page: 1 }),
  setStatus: (status) => set({ status, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setOrdering: (ordering) => set({ ordering }),
  reset: () => set(initialState),
}));
