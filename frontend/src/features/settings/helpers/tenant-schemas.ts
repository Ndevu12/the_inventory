import { z } from "zod"

const HEX_COLOR_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/

export function createTenantProfileSchema(messages: {
  nameRequired: string
  hexColor: string
}) {
  return z.object({
    name: z.string().min(1, messages.nameRequired).max(255),
    branding_site_name: z.string().max(255),
    branding_primary_color: z
      .string()
      .regex(HEX_COLOR_REGEX, messages.hexColor)
      .or(z.literal("")),
  })
}

export type TenantProfileFormValues = z.infer<
  ReturnType<typeof createTenantProfileSchema>
>
