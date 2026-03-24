import { z } from "zod"

export type CategorySchemaMessages = {
  nameRequired: string
  nameMax: string
  slugMax: string
}

export function createCategorySchema(messages: CategorySchemaMessages) {
  return z.object({
    name: z
      .string()
      .min(1, messages.nameRequired)
      .max(255, messages.nameMax),
    slug: z.string().max(255, messages.slugMax),
    description: z.string(),
    is_active: z.boolean(),
  })
}

export type CategoryFormValues = z.infer<ReturnType<typeof createCategorySchema>>
