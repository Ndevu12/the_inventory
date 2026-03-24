import { z } from "zod/v4";

export function createReservationSchema(messages: {
  productRequired: string;
  locationRequired: string;
  quantityRequired: string;
}) {
  return z.object({
    product: z.string().min(1, messages.productRequired),
    location: z.string().min(1, messages.locationRequired),
    quantity: z.string().min(1, messages.quantityRequired),
    sales_order: z.string(),
    notes: z.string(),
  });
}

export type CreateReservationFormValues = z.infer<
  ReturnType<typeof createReservationSchema>
>;
