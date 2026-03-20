import { z } from "zod"

export const soLineSchema = z.object({
  product: z.number().refine((val) => val >= 1, { message: "Product is required" }),
  quantity: z.number().refine((val) => val >= 1, { message: "Min 1" }),
  unit_price: z
    .string()
    .refine((v) => parseFloat(v) >= 0, { message: "Must be >= 0" }),
})

export const createSOSchema = z.object({
  order_number: z.string().min(1, "Order number is required").max(100),
  customer: z.number().refine((val) => val >= 1, { message: "Customer is required" }),
  order_date: z.string().min(1, "Order date is required"),
  notes: z.string(),
})

export type CreateSOFormValues = z.infer<typeof createSOSchema>
