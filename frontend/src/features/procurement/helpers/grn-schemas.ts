import { z } from "zod"

export interface CreateGRNSchemaMessages {
  grnNumberRequired: string
  purchaseOrderRequired: string
  receivedDateRequired: string
  locationRequired: string
}

export function buildCreateGRNSchema(messages: CreateGRNSchemaMessages) {
  return z.object({
    grn_number: z.string().min(1, messages.grnNumberRequired).max(100),
    purchase_order: z.coerce
      .number()
      .refine((val) => val > 0, { message: messages.purchaseOrderRequired }),
    received_date: z.string().min(1, messages.receivedDateRequired),
    location: z.coerce
      .number()
      .refine((val) => val > 0, { message: messages.locationRequired }),
    notes: z.string().optional().default(""),
  })
}

export type CreateGRNFormValues = z.infer<ReturnType<typeof buildCreateGRNSchema>>
