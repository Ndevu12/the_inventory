import { z } from "zod";

export const bulkTransferSchema = z.object({
  from_location: z.number().min(1, "Source location is required"),
  to_location: z.number().min(1, "Destination location is required"),
  reference: z.string(),
  notes: z.string(),
});

export type BulkTransferFormValues = z.infer<typeof bulkTransferSchema>;

export const bulkAdjustmentSchema = z.object({
  location: z.number().min(1, "Location is required"),
  notes: z.string(),
});

export type BulkAdjustmentFormValues = z.infer<typeof bulkAdjustmentSchema>;
