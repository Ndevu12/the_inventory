import { z } from "zod";

export function createCountLineSchema(messages: {
  quantityInt: string;
  quantityNonNegative: string;
}) {
  return z.object({
    quantity: z
      .number()
      .int(messages.quantityInt)
      .nonnegative(messages.quantityNonNegative),
    notes: z.string(),
  });
}

export type CountLineFormValues = z.infer<
  ReturnType<typeof createCountLineSchema>
>;
