import { z } from "zod/v4"

export type LocationSchemaMessages = {
  nameRequired: string
  nameMax: string
}

export function createLocationSchema(messages: LocationSchemaMessages) {
  return z.object({
    name: z.string().min(1, messages.nameRequired).max(255, messages.nameMax),
    description: z.string(),
    is_active: z.boolean(),
    max_capacity: z.string(),
  })
}

export type LocationFormValues = z.infer<ReturnType<typeof createLocationSchema>>
