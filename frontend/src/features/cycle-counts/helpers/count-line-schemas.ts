import { z } from "zod";

export const countLineSchema = z.object({
  quantity: z.number()
    .int("Quantity must be a whole number")
    .nonnegative("Quantity cannot be negative"),
  notes: z.string(),
});

export type CountLineFormValues = z.infer<typeof countLineSchema>;
