import { z } from "zod"

const paymentTermsEnum = z.enum(["net_30", "net_60", "net_90", "cod", "prepaid"])

export interface SupplierSchemaMessages {
  codeRequired: string
  nameRequired: string
  emailInvalid: string
  leadTimeMin: string
}

export function buildCreateSupplierSchema(messages: SupplierSchemaMessages) {
  return z.object({
    code: z.string().min(1, messages.codeRequired).max(100),
    name: z.string().min(1, messages.nameRequired).max(255),
    contact_name: z.string().max(255),
    email: z.string().email(messages.emailInvalid).or(z.literal("")),
    phone: z.string().max(50),
    address: z.string(),
    lead_time_days: z.number().int().min(0, messages.leadTimeMin),
    payment_terms: paymentTermsEnum,
    is_active: z.boolean(),
    notes: z.string(),
  })
}

export type CreateSupplierFormValues = z.infer<
  ReturnType<typeof buildCreateSupplierSchema>
>
export type EditSupplierFormValues = CreateSupplierFormValues
