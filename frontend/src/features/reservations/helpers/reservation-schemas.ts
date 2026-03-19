import { z } from "zod/v4";

export const createReservationSchema = z.object({
  product: z.string().min(1, "Product is required"),
  location: z.string().min(1, "Location is required"),
  quantity: z.string().min(1, "Quantity is required"),
  sales_order: z.string(),
  notes: z.string(),
});

export type CreateReservationFormValues = z.infer<typeof createReservationSchema>;
