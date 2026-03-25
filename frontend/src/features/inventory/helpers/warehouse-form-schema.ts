import { z } from "zod"

export interface WarehouseFormMessages {
  nameRequired: string
  nameMax: string
  timezoneRequired: string
}

export function createWarehouseSchema(messages: WarehouseFormMessages) {
  return z.object({
    name: z
      .string()
      .min(1, messages.nameRequired)
      .max(255, messages.nameMax),
    description: z.string(),
    is_active: z.boolean(),
    timezone_name: z.string().min(1, messages.timezoneRequired),
    address: z.string(),
  })
}

export type WarehouseFormValues = z.infer<
  ReturnType<typeof createWarehouseSchema>
>
