import { z } from "zod"

export const createDispatchSchema = z.object({
  dispatch_number: z.string().min(1, "Dispatch number is required").max(100),
  sales_order: z
    .number()
    .refine((val) => val > 0, { message: "Sales order is required" }),
  dispatch_date: z.string().min(1, "Dispatch date is required"),
  from_location: z
    .number()
    .refine((val) => val > 0, { message: "From location is required" }),
  notes: z.string().default(""),
})

export type CreateDispatchInput = z.input<typeof createDispatchSchema>
export type CreateDispatchFormValues = z.output<typeof createDispatchSchema>
