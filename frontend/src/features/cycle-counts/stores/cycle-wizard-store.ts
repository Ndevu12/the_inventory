import { create } from "zustand";
import type { VarianceResolution } from "../types/cycle-count.types";

export type WizardStep = "count" | "variances" | "reconcile";

export interface LineResolution {
  resolution: VarianceResolution;
  root_cause: string;
}

interface CycleWizardState {
  step: WizardStep;
  resolutions: Record<number, LineResolution>;
}

interface CycleWizardActions {
  setStep: (step: WizardStep) => void;
  setResolution: (lineId: number, resolution: LineResolution) => void;
  setBulkResolution: (lineIds: number[], resolution: VarianceResolution) => void;
  reset: () => void;
}

const initialState: CycleWizardState = {
  step: "count",
  resolutions: {},
};

export const useCycleWizardStore = create<
  CycleWizardState & CycleWizardActions
>()((set) => ({
  ...initialState,
  setStep: (step) => set({ step }),
  setResolution: (lineId, resolution) =>
    set((state) => ({
      resolutions: { ...state.resolutions, [lineId]: resolution },
    })),
  setBulkResolution: (lineIds, resolution) =>
    set((state) => {
      const updated = { ...state.resolutions };
      for (const id of lineIds) {
        updated[id] = {
          resolution,
          root_cause: updated[id]?.root_cause ?? "",
        };
      }
      return { resolutions: updated };
    }),
  reset: () => set(initialState),
}));
