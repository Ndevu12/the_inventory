import { z } from "zod";

export function createCycleSchema(messages: {
  nameRequired: string;
  scheduledRequired: string;
}) {
  return z.object({
    name: z.string().min(1, messages.nameRequired),
    location: z.string(),
    scheduled_date: z.string().min(1, messages.scheduledRequired),
    notes: z.string(),
  });
}

export type CreateCycleFormValues = z.infer<
  ReturnType<typeof createCycleSchema>
>;
