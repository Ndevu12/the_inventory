"use client"

import { useForm, useFieldArray } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
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
  createPurchaseOrderSchema,
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
  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreatePurchaseOrderFormValues>({
    resolver: zodResolver(createPurchaseOrderSchema),
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

  const watchedLines = watch("lines")

  const lineTotal = (index: number): number => {
    const line = watchedLines?.[index]
    if (!line) return 0
    const qty = Number(line.quantity) || 0
    const cost = Number(line.unit_cost) || 0
    return qty * cost
  }

  const grandTotal = watchedLines?.reduce((sum, _, i) => sum + lineTotal(i), 0) ?? 0

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Order Details</CardTitle>
          <CardDescription>Basic purchase order information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Supplier *</Label>
              <Select
                value={watch("supplier") ? watch("supplier").toString() : ""}
                onValueChange={(val) =>
                  setValue("supplier", Number(val), { shouldValidate: true })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a supplier..." />
                </SelectTrigger>
                <SelectContent>
                  {suppliers.map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.code} — {s.name}
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
              <Label htmlFor="order_date">Order Date *</Label>
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
                Expected Delivery Date
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
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              rows={3}
              placeholder="Internal notes about this order..."
              {...register("notes")}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Line Items</CardTitle>
              <CardDescription>
                Products to order from this supplier
              </CardDescription>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ product: 0, quantity: 1, unit_cost: "" })}
            >
              <PlusIcon className="mr-1 size-4" />
              Add Line
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
                  <TableHead className="w-[40%]">Product</TableHead>
                  <TableHead className="w-[15%]">Quantity</TableHead>
                  <TableHead className="w-[20%]">Unit Cost</TableHead>
                  <TableHead className="w-[15%] text-right">
                    Line Total
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
                          watch(`lines.${index}.product`)
                            ? watch(`lines.${index}.product`).toString()
                            : ""
                        }
                        onValueChange={(val) =>
                          setValue(`lines.${index}.product`, Number(val), {
                            shouldValidate: true,
                          })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select product..." />
                        </SelectTrigger>
                        <SelectContent>
                          {products.map((p) => (
                            <SelectItem key={p.id} value={p.id.toString()}>
                              {p.sku} — {p.name}
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
                        placeholder="0.00"
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
                    Grand Total
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
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create Purchase Order"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
