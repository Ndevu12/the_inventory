import { z } from "zod"

export const createGRNSchema = z.object({
  grn_number: z.string().min(1, "GRN number is required").max(100),
  purchase_order: z.coerce
    .number({ required_error: "Purchase order is required" })
    .positive("Purchase order is required"),
  received_date: z.string().min(1, "Received date is required"),
  location: z.coerce
    .number({ required_error: "Location is required" })
    .positive("Location is required"),
  notes: z.string().optional().default(""),
})

export type CreateGRNFormValues = z.infer<typeof createGRNSchema>
