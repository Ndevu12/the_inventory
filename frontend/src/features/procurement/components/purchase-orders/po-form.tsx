"use client"

import * as React from "react"
import { useForm, useFieldArray, useWatch } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useLocale, useTranslations } from "next-intl"
import { PlusIcon, TrashIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from "@/components/ui/table"

import {
  buildCreatePurchaseOrderSchema,
  type CreatePurchaseOrderFormValues,
} from "../../helpers/po-schemas"

interface SupplierOption {
  id: number
  name: string
  code: string
}

interface ProductOption {
  id: number
  name: string
  sku: string
}

interface POFormProps {
  suppliers: SupplierOption[]
  products: ProductOption[]
  onSubmit: (values: CreatePurchaseOrderFormValues) => void
  onCancel: () => void
  isSubmitting?: boolean
}

export function POForm({
  suppliers,
  products,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: POFormProps) {
  const locale = useLocale()
  const t = useTranslations("Procurement.purchaseOrders.form")
  const tVal = useTranslations("Procurement.purchaseOrders.validation")
  const tShared = useTranslations("Procurement.shared")
  const tCommon = useTranslations("Common.actions")

  const poSchema = React.useMemo(
    () =>
      buildCreatePurchaseOrderSchema({
        productRequired: tVal("productRequired"),
        quantityMin: tVal("quantityMin"),
        unitCostRequired: tVal("unitCostRequired"),
        unitCostPositive: tVal("unitCostPositive"),
        supplierRequired: tVal("supplierRequired"),
        orderDateRequired: tVal("orderDateRequired"),
        atLeastOneLine: tVal("atLeastOneLine"),
      }),
    [tVal],
  )

  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm<CreatePurchaseOrderFormValues>({
    resolver: zodResolver(poSchema),
    defaultValues: {
      supplier: 0,
      order_date: new Date().toISOString().split("T")[0],
      expected_delivery_date: "",
      notes: "",
      lines: [{ product: 0, quantity: 1, unit_cost: "" }],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "lines",
  })

  const watchedLines = useWatch({ control, name: "lines" })
  const supplierId = useWatch({ control, name: "supplier" })

  const lineTotal = (index: number): number => {
    const line = watchedLines?.[index]
    if (!line) return 0
    const qty = Number(line.quantity) || 0
    const cost = Number(line.unit_cost) || 0
    return qty * cost
  }

  const grandTotal = watchedLines?.reduce((sum, _, i) => sum + lineTotal(i), 0) ?? 0

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat(locale, { style: "currency", currency: "USD" }).format(value)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("orderDetailsTitle")}</CardTitle>
          <CardDescription>{t("orderDetailsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>
                {t("supplier")} <span className="text-destructive">*</span>
              </Label>
              <Select
                value={supplierId ? supplierId.toString() : ""}
                onValueChange={(val) =>
                  setValue("supplier", Number(val), { shouldValidate: true })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("selectSupplier")} />
                </SelectTrigger>
                <SelectContent>
                  {suppliers.map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.code}
                      {tShared("nameSeparator")}
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.supplier && (
                <p className="text-xs text-destructive">
                  {errors.supplier.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="order_date">
                {t("orderDate")} <span className="text-destructive">*</span>
              </Label>
              <Input
                id="order_date"
                type="date"
                {...register("order_date")}
              />
              {errors.order_date && (
                <p className="text-xs text-destructive">
                  {errors.order_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="expected_delivery_date">
                {t("expectedDeliveryDate")}
              </Label>
              <Input
                id="expected_delivery_date"
                type="date"
                {...register("expected_delivery_date")}
              />
              {errors.expected_delivery_date && (
                <p className="text-xs text-destructive">
                  {errors.expected_delivery_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">{t("notes")}</Label>
            <Textarea
              id="notes"
              rows={3}
              placeholder={t("notesPlaceholder")}
              {...register("notes")}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{t("lineItemsTitle")}</CardTitle>
              <CardDescription>{t("lineItemsDescription")}</CardDescription>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ product: 0, quantity: 1, unit_cost: "" })}
            >
              <PlusIcon className="mr-1 size-4" />
              {t("addLine")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {errors.lines?.root && (
            <p className="mb-4 text-sm text-destructive">
              {errors.lines.root.message}
            </p>
          )}
          {errors.lines?.message && (
            <p className="mb-4 text-sm text-destructive">
              {errors.lines.message}
            </p>
          )}

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40%]">{t("colProduct")}</TableHead>
                  <TableHead className="w-[15%]">{t("colQuantity")}</TableHead>
                  <TableHead className="w-[20%]">{t("colUnitCost")}</TableHead>
                  <TableHead className="w-[15%] text-right">
                    {t("colLineTotal")}
                  </TableHead>
                  <TableHead className="w-[10%]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {fields.map((field, index) => (
                  <TableRow key={field.id}>
                    <TableCell>
                      <Select
                        value={
                          watchedLines?.[index]?.product
                            ? String(watchedLines[index].product)
                            : ""
                        }
                        onValueChange={(val) =>
                          setValue(`lines.${index}.product`, Number(val), {
                            shouldValidate: true,
                          })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder={t("selectProduct")} />
                        </SelectTrigger>
                        <SelectContent>
                          {products.map((p) => (
                            <SelectItem key={p.id} value={p.id.toString()}>
                              {p.sku}
                              {tShared("nameSeparator")}
                              {p.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.lines?.[index]?.product && (
                        <p className="mt-1 text-xs text-destructive">
                          {errors.lines[index].product.message}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        min={1}
                        className="w-full"
                        {...register(`lines.${index}.quantity`, {
                          valueAsNumber: true,
                        })}
                      />
                      {errors.lines?.[index]?.quantity && (
                        <p className="mt-1 text-xs text-destructive">
                          {errors.lines[index].quantity.message}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Input
                        type="text"
                        inputMode="decimal"
                        placeholder={t("unitCostPlaceholder")}
                        className="w-full"
                        {...register(`lines.${index}.unit_cost`)}
                      />
                      {errors.lines?.[index]?.unit_cost && (
                        <p className="mt-1 text-xs text-destructive">
                          {errors.lines[index].unit_cost.message}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(lineTotal(index))}
                    </TableCell>
                    <TableCell>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="size-8 text-muted-foreground hover:text-destructive"
                        onClick={() => remove(index)}
                        disabled={fields.length <= 1}
                      >
                        <TrashIcon className="size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={3} className="text-right font-semibold">
                    {t("grandTotal")}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {formatCurrency(grandTotal)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableFooter>
            </Table>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            {tCommon("cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t("creating") : t("submit")}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
