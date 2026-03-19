import { create } from "zustand"

export interface LineItemRow {
  id: string
  product: number | null
  quantity: number
  unit_cost: string
}

let nextId = 1
function generateId(): string {
  return `line-${nextId++}`
}

interface POLineItemsState {
  lines: LineItemRow[]
  addLine: () => void
  removeLine: (id: string) => void
  updateLine: (id: string, updates: Partial<Omit<LineItemRow, "id">>) => void
  reset: () => void
  setLines: (lines: LineItemRow[]) => void
}

const createEmptyLine = (): LineItemRow => ({
  id: generateId(),
  product: null,
  quantity: 1,
  unit_cost: "",
})

export const usePOLineItemsStore = create<POLineItemsState>((set) => ({
  lines: [createEmptyLine()],

  addLine: () =>
    set((state) => ({
      lines: [...state.lines, createEmptyLine()],
    })),

  removeLine: (id) =>
    set((state) => ({
      lines: state.lines.filter((l) => l.id !== id),
    })),

  updateLine: (id, updates) =>
    set((state) => ({
      lines: state.lines.map((l) =>
        l.id === id ? { ...l, ...updates } : l,
      ),
    })),

  reset: () => {
    nextId = 1
    set({ lines: [createEmptyLine()] })
  },

  setLines: (lines) => set({ lines }),
}))
