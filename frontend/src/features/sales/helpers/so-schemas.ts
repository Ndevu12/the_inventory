import { z } from "zod"

export const soLineSchema = z.object({
  product: z.number({ required_error: "Product is required" }).min(1, "Product is required"),
  quantity: z.number({ required_error: "Quantity is required" }).min(1, "Min 1"),
  unit_price: z
    .string({ required_error: "Price is required" })
    .refine((v) => parseFloat(v) >= 0, "Must be >= 0"),
})

export const createSOSchema = z.object({
  order_number: z.string().min(1, "Order number is required").max(100),
  customer: z.number({ required_error: "Customer is required" }).min(1, "Customer is required"),
  order_date: z.string().min(1, "Order date is required"),
  notes: z.string(),
})

export type CreateSOFormValues = z.infer<typeof createSOSchema>
