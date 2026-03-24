import { z } from "zod"

export interface CustomerSchemaMessages {
  nameRequired: string
  emailInvalid: string
}

export function buildCreateCustomerSchema(messages: CustomerSchemaMessages) {
  return z.object({
    code: z.string().max(100),
    name: z.string().min(1, messages.nameRequired).max(255),
    contact_name: z.string().max(255),
    email: z.string().email(messages.emailInvalid).or(z.literal("")),
    phone: z.string().max(50),
    address: z.string(),
    is_active: z.boolean(),
    notes: z.string(),
  })
}

export type CreateCustomerFormValues = z.infer<
  ReturnType<typeof buildCreateCustomerSchema>
>
export type EditCustomerFormValues = CreateCustomerFormValues
