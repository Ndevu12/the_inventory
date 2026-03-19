import { create } from "zustand";

// ─── Transfer ────────────────────────────────────────────────────────────────

export interface TransferLine {
  id: string;
  product_id: number | null;
  quantity: number;
}

interface TransferItemsState {
  lines: TransferLine[];
  addLine: () => void;
  removeLine: (id: string) => void;
  updateLine: (id: string, updates: Partial<Omit<TransferLine, "id">>) => void;
  reset: () => void;
}

let transferKey = 1;

function createTransferLine(): TransferLine {
  return { id: `t-${transferKey++}`, product_id: null, quantity: 1 };
}

export const useTransferItemsStore = create<TransferItemsState>((set) => ({
  lines: [createTransferLine()],

  addLine: () =>
    set((s) => ({ lines: [...s.lines, createTransferLine()] })),

  removeLine: (id) =>
    set((s) => ({
      lines: s.lines.length > 1 ? s.lines.filter((l) => l.id !== id) : s.lines,
    })),

  updateLine: (id, updates) =>
    set((s) => ({
      lines: s.lines.map((l) => (l.id === id ? { ...l, ...updates } : l)),
    })),

  reset: () => {
    transferKey = 1;
    set({ lines: [createTransferLine()] });
  },
}));

// ─── Adjustment ──────────────────────────────────────────────────────────────

export interface AdjustmentLine {
  id: string;
  product_id: number | null;
  new_quantity: number;
}

interface AdjustmentItemsState {
  lines: AdjustmentLine[];
  addLine: () => void;
  removeLine: (id: string) => void;
  updateLine: (id: string, updates: Partial<Omit<AdjustmentLine, "id">>) => void;
  reset: () => void;
}

let adjustmentKey = 1;

function createAdjustmentLine(): AdjustmentLine {
  return { id: `a-${adjustmentKey++}`, product_id: null, new_quantity: 0 };
}

export const useAdjustmentItemsStore = create<AdjustmentItemsState>((set) => ({
  lines: [createAdjustmentLine()],

  addLine: () =>
    set((s) => ({ lines: [...s.lines, createAdjustmentLine()] })),

  removeLine: (id) =>
    set((s) => ({
      lines: s.lines.length > 1 ? s.lines.filter((l) => l.id !== id) : s.lines,
    })),

  updateLine: (id, updates) =>
    set((s) => ({
      lines: s.lines.map((l) => (l.id === id ? { ...l, ...updates } : l)),
    })),

  reset: () => {
    adjustmentKey = 1;
    set({ lines: [createAdjustmentLine()] });
  },
}));

// ─── Revalue ─────────────────────────────────────────────────────────────────

export interface RevalueLine {
  id: string;
  product_id: number | null;
  new_unit_cost: string;
}

interface RevalueItemsState {
  lines: RevalueLine[];
  addLine: () => void;
  removeLine: (id: string) => void;
  updateLine: (id: string, updates: Partial<Omit<RevalueLine, "id">>) => void;
  reset: () => void;
}

let revalueKey = 1;

function createRevalueLine(): RevalueLine {
  return { id: `r-${revalueKey++}`, product_id: null, new_unit_cost: "" };
}

export const useRevalueItemsStore = create<RevalueItemsState>((set) => ({
  lines: [createRevalueLine()],

  addLine: () =>
    set((s) => ({ lines: [...s.lines, createRevalueLine()] })),

  removeLine: (id) =>
    set((s) => ({
      lines: s.lines.length > 1 ? s.lines.filter((l) => l.id !== id) : s.lines,
    })),

  updateLine: (id, updates) =>
    set((s) => ({
      lines: s.lines.map((l) => (l.id === id ? { ...l, ...updates } : l)),
    })),

  reset: () => {
    revalueKey = 1;
    set({ lines: [createRevalueLine()] });
  },
}));
