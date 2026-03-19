import { z } from "zod";

export const countLineSchema = z.object({
  quantity: z.coerce
    .number({ invalid_type_error: "Quantity must be a number" })
    .int("Quantity must be a whole number")
    .nonnegative("Quantity cannot be negative"),
  notes: z.string().optional().default(""),
});

export type CountLineFormValues = z.infer<typeof countLineSchema>;
