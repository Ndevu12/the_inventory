import { create } from "zustand"

export interface LineItemRow {
  key: string
  product: number | null
  productLabel: string
  quantity: number
  unitPrice: string
  lineTotal: string
}

function calcLineTotal(qty: number, price: string): string {
  const total = qty * parseFloat(price || "0")
  return isNaN(total) ? "0.00" : total.toFixed(2)
}

let nextKey = 1
function generateKey(): string {
  return `line-${nextKey++}`
}

interface SOLineItemsState {
  items: LineItemRow[]
  addItem: () => void
  removeItem: (key: string) => void
  updateItem: (key: string, updates: Partial<Omit<LineItemRow, "key" | "lineTotal">>) => void
  reset: () => void
  orderTotal: () => string
}

function createEmptyItem(): LineItemRow {
  return {
    key: generateKey(),
    product: null,
    productLabel: "",
    quantity: 1,
    unitPrice: "0.00",
    lineTotal: "0.00",
  }
}

export const useSOLineItemsStore = create<SOLineItemsState>((set, get) => ({
  items: [createEmptyItem()],

  addItem: () =>
    set((state) => ({ items: [...state.items, createEmptyItem()] })),

  removeItem: (key) =>
    set((state) => ({
      items: state.items.length > 1
        ? state.items.filter((i) => i.key !== key)
        : state.items,
    })),

  updateItem: (key, updates) =>
    set((state) => ({
      items: state.items.map((item) => {
        if (item.key !== key) return item
        const merged = { ...item, ...updates }
        return {
          ...merged,
          lineTotal: calcLineTotal(merged.quantity, merged.unitPrice),
        }
      }),
    })),

  reset: () => {
    nextKey = 1
    set({ items: [createEmptyItem()] })
  },

  orderTotal: () => {
    const total = get().items.reduce(
      (sum, item) => sum + parseFloat(item.lineTotal || "0"),
      0,
    )
    return total.toFixed(2)
  },
}))
