import { z } from "zod";

export const createCycleSchema = z.object({
  name: z.string().min(1, "Name is required"),
  location: z.string(),
  scheduled_date: z.string().min(1, "Scheduled date is required"),
  notes: z.string(),
});

export type CreateCycleFormValues = z.infer<typeof createCycleSchema>;

export const recordCountSchema = z.object({
  counted_quantity: z.string().min(1, "Counted quantity is required"),
  notes: z.string(),
});

export type RecordCountFormValues = z.infer<typeof recordCountSchema>;
