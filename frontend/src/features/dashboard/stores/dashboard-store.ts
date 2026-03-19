import { create } from "zustand";

interface DashboardState {
  orderChartTab: "purchase" | "sales";
  setOrderChartTab: (tab: "purchase" | "sales") => void;
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  orderChartTab: "purchase",
  setOrderChartTab: (tab) => set({ orderChartTab: tab }),
}));
