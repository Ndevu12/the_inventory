import { z } from "zod"

export interface CreateSOSchemaMessages {
  customerRequired: string
  orderDateRequired: string
}

export function buildCreateSOSchema(messages: CreateSOSchemaMessages) {
  return z.object({
    order_number: z.string().max(100).optional().nullable(),
    customer: z
      .number()
      .refine((val) => val >= 1, { message: messages.customerRequired }),
    order_date: z.string().min(1, messages.orderDateRequired),
    notes: z.string(),
  })
}

export type CreateSOFormValues = z.infer<ReturnType<typeof buildCreateSOSchema>>
