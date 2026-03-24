export const UNIT_OF_MEASURE_VALUES = [
  "pcs",
  "kg",
  "lt",
  "m",
  "box",
  "pack",
] as const

export type UnitOfMeasureValue = (typeof UNIT_OF_MEASURE_VALUES)[number]

export const TRACKING_MODE_VALUES = ["none", "optional", "required"] as const

export type TrackingModeValue = (typeof TRACKING_MODE_VALUES)[number]

export const ACTIVE_STATUS_VALUES = ["true", "false"] as const
