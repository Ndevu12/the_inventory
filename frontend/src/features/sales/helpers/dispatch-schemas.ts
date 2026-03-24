import { z } from "zod"

export interface CreateDispatchSchemaMessages {
  salesOrderRequired: string
  dispatchDateRequired: string
  fromLocationRequired: string
}

export function buildCreateDispatchSchema(messages: CreateDispatchSchemaMessages) {
  return z.object({
    dispatch_number: z.string().max(100),
    sales_order: z
      .number()
      .refine((val) => val > 0, { message: messages.salesOrderRequired }),
    dispatch_date: z.string().min(1, messages.dispatchDateRequired),
    from_location: z
      .number()
      .refine((val) => val > 0, { message: messages.fromLocationRequired }),
    notes: z.string().default(""),
  })
}

export type CreateDispatchInput = z.input<
  ReturnType<typeof buildCreateDispatchSchema>
>
export type CreateDispatchFormValues = z.output<
  ReturnType<typeof buildCreateDispatchSchema>
>
