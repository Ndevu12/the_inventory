export const UNITS_OF_MEASURE = [
  { value: "pcs", label: "Pieces" },
  { value: "kg", label: "Kilograms" },
  { value: "lt", label: "Litres" },
  { value: "m", label: "Metres" },
  { value: "box", label: "Boxes" },
  { value: "pack", label: "Packs" },
] as const

export const TRACKING_MODES = [
  { value: "none", label: "No Tracking" },
  { value: "optional", label: "Optional" },
  { value: "required", label: "Required" },
] as const

export const MOVEMENT_TYPES = [
  { value: "receive", label: "Receive" },
  { value: "issue", label: "Issue" },
  { value: "transfer", label: "Transfer" },
  { value: "adjustment", label: "Adjustment" },
] as const

export const ACTIVE_STATUS_OPTIONS = [
  { value: "true", label: "Active" },
  { value: "false", label: "Inactive" },
] as const
