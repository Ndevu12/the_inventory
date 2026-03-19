import { z } from "zod"

const paymentTermsEnum = z.enum(["net_30", "net_60", "net_90", "cod", "prepaid"])

export const createSupplierSchema = z.object({
  code: z.string().min(1, "Code is required").max(100),
  name: z.string().min(1, "Name is required").max(255),
  contact_name: z.string().max(255),
  email: z.string().email("Invalid email address").or(z.literal("")),
  phone: z.string().max(50),
  address: z.string(),
  lead_time_days: z.number().int().min(0, "Must be 0 or greater"),
  payment_terms: paymentTermsEnum,
  is_active: z.boolean(),
  notes: z.string(),
})

export const editSupplierSchema = createSupplierSchema

export type CreateSupplierFormValues = z.infer<typeof createSupplierSchema>
export type EditSupplierFormValues = z.infer<typeof editSupplierSchema>
