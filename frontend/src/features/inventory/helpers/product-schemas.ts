import { z } from "zod"

export type ProductSchemaMessages = {
  skuRequired: string
  skuMax: string
  nameRequired: string
  nameMax: string
  unitOfMeasureRequired: string
  unitCostMin: string
  reorderPointInt: string
  reorderPointMin: string
}

export function createProductSchema(messages: ProductSchemaMessages) {
  return z.object({
    sku: z
      .string()
      .min(1, messages.skuRequired)
      .max(100, messages.skuMax),
    name: z
      .string()
      .min(1, messages.nameRequired)
      .max(255, messages.nameMax),
    description: z.string(),
    category: z.number().nullable(),
    unit_of_measure: z.string().min(1, messages.unitOfMeasureRequired),
    unit_cost: z.number().min(0, messages.unitCostMin),
    reorder_point: z
      .number()
      .int(messages.reorderPointInt)
      .min(0, messages.reorderPointMin),
    tracking_mode: z.string(),
    is_active: z.boolean(),
  })
}

export type ProductSchemaValues = z.infer<ReturnType<typeof createProductSchema>>
