import { z } from "zod"

const HEX_COLOR_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/

export const tenantProfileSchema = z.object({
  name: z.string().min(1, "Tenant name is required").max(255),
  branding_site_name: z.string().max(255),
  branding_primary_color: z
    .string()
    .regex(HEX_COLOR_REGEX, "Must be a valid hex color (e.g. #3B82F6)")
    .or(z.literal("")),
})

export type TenantProfileFormValues = z.infer<typeof tenantProfileSchema>
