import { z } from "zod";

export function createBulkTransferSchema(messages: {
  sourceLocationRequired: string;
  destinationLocationRequired: string;
}) {
  return z.object({
    from_location: z
      .number()
      .min(1, messages.sourceLocationRequired),
    to_location: z
      .number()
      .min(1, messages.destinationLocationRequired),
    reference: z.string(),
    notes: z.string(),
  });
}

export type BulkTransferFormValues = z.infer<
  ReturnType<typeof createBulkTransferSchema>
>;

export function createBulkAdjustmentSchema(messages: {
  locationRequired: string;
}) {
  return z.object({
    location: z.number().min(1, messages.locationRequired),
    notes: z.string(),
  });
}

export type BulkAdjustmentFormValues = z.infer<
  ReturnType<typeof createBulkAdjustmentSchema>
>;
