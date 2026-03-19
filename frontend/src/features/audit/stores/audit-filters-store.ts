import { create } from "zustand"

interface AuditFiltersState {
  action: string
  dateFrom: string
  dateTo: string
  page: number
  pageSize: number
  ordering: string
}

interface AuditFiltersActions {
  setAction: (action: string) => void
  setDateFrom: (dateFrom: string) => void
  setDateTo: (dateTo: string) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  setOrdering: (ordering: string) => void
  reset: () => void
}

const initialState: AuditFiltersState = {
  action: "",
  dateFrom: "",
  dateTo: "",
  page: 1,
  pageSize: 25,
  ordering: "-timestamp",
}

export const useAuditFiltersStore = create<
  AuditFiltersState & AuditFiltersActions
>()((set) => ({
  ...initialState,
  setAction: (action) => set({ action, page: 1 }),
  setDateFrom: (dateFrom) => set({ dateFrom, page: 1 }),
  setDateTo: (dateTo) => set({ dateTo, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setOrdering: (ordering) => set({ ordering }),
  reset: () => set(initialState),
}))
