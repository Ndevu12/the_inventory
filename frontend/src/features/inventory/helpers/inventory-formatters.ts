import { UNITS_OF_MEASURE, TRACKING_MODES, MOVEMENT_TYPES } from "./inventory-constants"

export function formatUnitOfMeasure(value: string): string {
  return UNITS_OF_MEASURE.find((u) => u.value === value)?.label ?? value
}

export function formatTrackingMode(value: string): string {
  return TRACKING_MODES.find((t) => t.value === value)?.label ?? value
}

export function formatMovementType(value: string): string {
  return MOVEMENT_TYPES.find((m) => m.value === value)?.label ?? value
}

export function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(dateString))
}

export function formatDateTime(dateString: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateString))
}
