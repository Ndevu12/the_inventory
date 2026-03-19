import { create } from "zustand"
import type { ReportPeriod, ValuationMethod, VarianceType } from "../types/reports.types"

interface ReportFiltersState {
  dateFrom: string
  dateTo: string
  period: ReportPeriod
  valuationMethod: ValuationMethod
  movementType: string
  threshold: number
  daysAhead: number
  varianceType: string
  productSku: string
  lotNumber: string
  categoryId: string
  productId: string
}

interface ReportFiltersActions {
  setDateFrom: (dateFrom: string) => void
  setDateTo: (dateTo: string) => void
  setPeriod: (period: ReportPeriod) => void
  setValuationMethod: (method: ValuationMethod) => void
  setMovementType: (type: string) => void
  setThreshold: (threshold: number) => void
  setDaysAhead: (days: number) => void
  setVarianceType: (type: string) => void
  setProductSku: (sku: string) => void
  setLotNumber: (lot: string) => void
  setCategoryId: (id: string) => void
  setProductId: (id: string) => void
  reset: () => void
}

const initialState: ReportFiltersState = {
  dateFrom: "",
  dateTo: "",
  period: "monthly",
  valuationMethod: "weighted_average",
  movementType: "",
  threshold: 3,
  daysAhead: 30,
  varianceType: "",
  productSku: "",
  lotNumber: "",
  categoryId: "",
  productId: "",
}

export const useReportFiltersStore = create<
  ReportFiltersState & ReportFiltersActions
>()((set) => ({
  ...initialState,

  setDateFrom: (dateFrom) => set({ dateFrom }),
  setDateTo: (dateTo) => set({ dateTo }),
  setPeriod: (period) => set({ period }),
  setValuationMethod: (valuationMethod) => set({ valuationMethod }),
  setMovementType: (movementType) => set({ movementType }),
  setThreshold: (threshold) => set({ threshold }),
  setDaysAhead: (daysAhead) => set({ daysAhead }),
  setVarianceType: (varianceType) => set({ varianceType }),
  setProductSku: (productSku) => set({ productSku }),
  setLotNumber: (lotNumber) => set({ lotNumber }),
  setCategoryId: (categoryId) => set({ categoryId }),
  setProductId: (productId) => set({ productId }),
  reset: () => set(initialState),
}))
