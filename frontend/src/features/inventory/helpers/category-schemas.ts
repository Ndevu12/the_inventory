import { z } from "zod";

export const categorySchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(255, "Name must be 255 characters or less"),
  slug: z.string().max(255, "Slug must be 255 characters or less"),
  description: z.string(),
  is_active: z.boolean(),
});

export type CategoryFormValues = z.infer<typeof categorySchema>;
