import { z } from "zod"

export const productSchema = z.object({
  sku: z
    .string()
    .min(1, "SKU is required")
    .max(100, "SKU must be 100 characters or less"),
  name: z
    .string()
    .min(1, "Name is required")
    .max(255, "Name must be 255 characters or less"),
  description: z.string(),
  category: z.number().nullable(),
  unit_of_measure: z.string().min(1, "Unit of measure is required"),
  unit_cost: z.number().min(0, "Unit cost must be zero or greater"),
  reorder_point: z
    .number()
    .int("Reorder point must be a whole number")
    .min(0, "Reorder point must be zero or greater"),
  tracking_mode: z.string(),
  is_active: z.boolean(),
})

export type ProductSchemaValues = z.infer<typeof productSchema>
