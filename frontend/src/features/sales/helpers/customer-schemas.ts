import { z } from "zod"

export const createCustomerSchema = z.object({
  code: z.string().max(100),
  name: z.string().min(1, "Name is required").max(255),
  contact_name: z.string().max(255),
  email: z.string().email("Invalid email address").or(z.literal("")),
  phone: z.string().max(50),
  address: z.string(),
  is_active: z.boolean(),
  notes: z.string(),
})

export const editCustomerSchema = createCustomerSchema

export type CreateCustomerFormValues = z.infer<typeof createCustomerSchema>
export type EditCustomerFormValues = z.infer<typeof editCustomerSchema>
