import { z } from "zod"

export const createDispatchSchema = z.object({
  dispatch_number: z.string().min(1, "Dispatch number is required").max(100),
  sales_order: z
    .number({ required_error: "Sales order is required" })
    .positive("Sales order is required"),
  dispatch_date: z.string().min(1, "Dispatch date is required"),
  from_location: z
    .number({ required_error: "From location is required" })
    .positive("From location is required"),
  notes: z.string().default(""),
})

export type CreateDispatchInput = z.input<typeof createDispatchSchema>
export type CreateDispatchFormValues = z.output<typeof createDispatchSchema>
