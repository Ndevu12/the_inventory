import { create } from "zustand"
import { DEFAULT_PAGE_SIZE } from "@/lib/utils/constants"

interface ProductFiltersState {
  search: string
  category: string
  isActive: string
  page: number
  pageSize: number
  ordering: string
}

interface ProductFiltersActions {
  setSearch: (search: string) => void
  setCategory: (category: string) => void
  setIsActive: (isActive: string) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  setOrdering: (ordering: string) => void
  reset: () => void
}

const initialState: ProductFiltersState = {
  search: "",
  category: "",
  isActive: "",
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  ordering: "sku",
}

export const useProductFiltersStore = create<
  ProductFiltersState & ProductFiltersActions
>()((set) => ({
  ...initialState,

  setSearch: (search) => set({ search, page: 1 }),
  setCategory: (category) => set({ category, page: 1 }),
  setIsActive: (isActive) => set({ isActive, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setOrdering: (ordering) => set({ ordering }),
  reset: () => set(initialState),
}))
