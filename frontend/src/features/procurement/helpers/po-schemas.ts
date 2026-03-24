import { z } from "zod"

export interface POLineSchemaMessages {
  productRequired: string
  quantityMin: string
  unitCostRequired: string
  unitCostPositive: string
}

export function buildPoLineSchema(messages: POLineSchemaMessages) {
  return z.object({
    product: z.number().min(1, messages.productRequired),
    quantity: z.number().int().min(1, messages.quantityMin),
    unit_cost: z.string().min(1, messages.unitCostRequired).refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0,
      messages.unitCostPositive,
    ),
  })
}

export interface CreatePurchaseOrderSchemaMessages extends POLineSchemaMessages {
  supplierRequired: string
  orderDateRequired: string
  atLeastOneLine: string
}

export function buildCreatePurchaseOrderSchema(messages: CreatePurchaseOrderSchemaMessages) {
  const line = buildPoLineSchema(messages)
  return z.object({
    supplier: z.number().min(1, messages.supplierRequired),
    order_date: z.string().min(1, messages.orderDateRequired),
    expected_delivery_date: z.string(),
    notes: z.string(),
    lines: z.array(line).min(1, messages.atLeastOneLine),
  })
}

export type POLineFormValues = z.infer<ReturnType<typeof buildPoLineSchema>>
export type CreatePurchaseOrderFormValues = z.infer<
  ReturnType<typeof buildCreatePurchaseOrderSchema>
>
