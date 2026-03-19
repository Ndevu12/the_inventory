import { create } from "zustand";
import type { MovementType } from "../api/movements-api";

interface MovementFormState {
  movementType: MovementType;
  setMovementType: (type: MovementType) => void;
  enableLotFields: boolean;
  setEnableLotFields: (enabled: boolean) => void;
  reset: () => void;
}

export const useMovementFormStore = create<MovementFormState>((set) => ({
  movementType: "receive",
  setMovementType: (type) => set({ movementType: type }),
  enableLotFields: false,
  setEnableLotFields: (enabled) => set({ enableLotFields: enabled }),
  reset: () =>
    set({ movementType: "receive", enableLotFields: false }),
}));
