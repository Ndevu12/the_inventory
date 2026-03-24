import { z } from "zod"
import type { MovementType } from "../api/movements-api"

export const MOVEMENT_TYPE_VALUES: MovementType[] = [
  "receive",
  "issue",
  "transfer",
  "adjustment",
]

export const ALLOCATION_STRATEGY_VALUES = ["FIFO", "LIFO"] as const

export type MovementFormSchemaMessages = {
  productRequired: string
  quantityMin: string
  receiveToRequired: string
  issueFromRequired: string
  transferFromRequired: string
  transferToRequired: string
  transferLocationsDiffer: string
  adjustmentLocationRequired: string
}

export function createMovementFormSchema(messages: MovementFormSchemaMessages) {
  const movementTypeEnum = z.enum([
    "receive",
    "issue",
    "transfer",
    "adjustment",
  ])

  return z
    .object({
      product: z.number().min(1, messages.productRequired),
      movement_type: movementTypeEnum,
      quantity: z.number().int().min(1, messages.quantityMin),
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
              message: messages.receiveToRequired,
              path: ["to_location"],
            })
          }
          break
        case "issue":
          if (!data.from_location) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: messages.issueFromRequired,
              path: ["from_location"],
            })
          }
          break
        case "transfer":
          if (!data.from_location) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: messages.transferFromRequired,
              path: ["from_location"],
            })
          }
          if (!data.to_location) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: messages.transferToRequired,
              path: ["to_location"],
            })
          }
          if (
            data.from_location &&
            data.to_location &&
            data.from_location === data.to_location
          ) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: messages.transferLocationsDiffer,
              path: ["to_location"],
            })
          }
          break
        case "adjustment":
          if (!data.from_location && !data.to_location) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: messages.adjustmentLocationRequired,
              path: ["from_location"],
            })
          }
          break
      }
    })
}

export type MovementFormValues = z.infer<
  ReturnType<typeof createMovementFormSchema>
>

export function showFromLocation(type: MovementType): boolean {
  return type === "issue" || type === "transfer" || type === "adjustment"
}

export function showToLocation(type: MovementType): boolean {
  return type === "receive" || type === "transfer" || type === "adjustment"
}

export function showLotFields(type: MovementType): boolean {
  return type === "receive"
}

export function showAllocationStrategy(type: MovementType): boolean {
  return type === "issue" || type === "transfer"
}
