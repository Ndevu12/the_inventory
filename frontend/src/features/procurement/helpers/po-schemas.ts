import { z } from "zod"

export const poLineSchema = z.object({
  product: z.number().min(1, "Product is required"),
  quantity: z.coerce.number().int().min(1, "Quantity must be at least 1"),
  unit_cost: z.string().min(1, "Unit cost is required").refine(
    (v) => !isNaN(Number(v)) && Number(v) > 0,
    "Must be a positive number",
  ),
})

export const createPurchaseOrderSchema = z.object({
  supplier: z.coerce.number().min(1, "Supplier is required"),
  order_date: z.string().min(1, "Order date is required"),
  expected_delivery_date: z.string().optional().default(""),
  notes: z.string().optional().default(""),
  lines: z.array(poLineSchema).min(1, "At least one line item is required"),
})

export type POLineFormValues = z.infer<typeof poLineSchema>
export type CreatePurchaseOrderFormValues = z.infer<typeof createPurchaseOrderSchema>
