import { z } from "zod";
import type { MovementType } from "../api/movements-api";

export const MOVEMENT_TYPES: { value: MovementType; label: string }[] = [
  { value: "receive", label: "Receive" },
  { value: "issue", label: "Issue" },
  { value: "transfer", label: "Transfer" },
  { value: "adjustment", label: "Adjustment" },
];

export const ALLOCATION_STRATEGIES = [
  { value: "FIFO", label: "FIFO (First In, First Out)" },
  { value: "LIFO", label: "LIFO (Last In, First Out)" },
] as const;

const movementTypeEnum = z.enum(["receive", "issue", "transfer", "adjustment"]);

export const movementFormSchema = z
  .object({
    product: z.number().min(1, "Product is required"),
    movement_type: movementTypeEnum,
    quantity: z.number().int().min(1, "Quantity must be at least 1"),
    from_location: z.number().optional(),
    to_location: z.number().optional(),
    unit_cost: z.string().optional(),
    reference: z.string().optional(),
    notes: z.string().optional(),
    lot_number: z.string().optional(),
    serial_number: z.string().optional(),
    manufacturing_date: z.string().optional(),
    expiry_date: z.string().optional(),
    allocation_strategy: z.enum(["FIFO", "LIFO"]).optional(),
  })
  .superRefine((data, ctx) => {
    switch (data.movement_type) {
      case "receive":
        if (!data.to_location) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Destination location is required for receive movements",
            path: ["to_location"],
          });
        }
        break;
      case "issue":
        if (!data.from_location) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Source location is required for issue movements",
            path: ["from_location"],
          });
        }
        break;
      case "transfer":
        if (!data.from_location) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Source location is required for transfers",
            path: ["from_location"],
          });
        }
        if (!data.to_location) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Destination location is required for transfers",
            path: ["to_location"],
          });
        }
        if (
          data.from_location &&
          data.to_location &&
          data.from_location === data.to_location
        ) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Source and destination must differ",
            path: ["to_location"],
          });
        }
        break;
      case "adjustment":
        if (!data.from_location && !data.to_location) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "At least one location is required for adjustments",
            path: ["from_location"],
          });
        }
        break;
    }
  });

export type MovementFormValues = z.infer<typeof movementFormSchema>;

export function showFromLocation(type: MovementType): boolean {
  return type === "issue" || type === "transfer" || type === "adjustment";
}

export function showToLocation(type: MovementType): boolean {
  return type === "receive" || type === "transfer" || type === "adjustment";
}

export function showLotFields(type: MovementType): boolean {
  return type === "receive";
}

export function showAllocationStrategy(type: MovementType): boolean {
  return type === "issue" || type === "transfer";
}
