"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { PlusIcon, TrashIcon } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useSOLineItemsStore } from "../../stores/so-line-items-store"
import { createSOSchema, type CreateSOFormValues } from "../../helpers/so-schemas"
import type { SimpleProduct, SimpleCustomer, SalesOrderCreatePayload } from "../../types/sales.types"

interface SOFormProps {
  products: SimpleProduct[]
  productsLoading: boolean
  customers: SimpleCustomer[]
  customersLoading: boolean
  onSubmit: (payload: SalesOrderCreatePayload) => void
  isSubmitting: boolean
  onCancel: () => void
}

export function SOForm({
  products,
  productsLoading,
  customers,
  customersLoading,
  onSubmit,
  isSubmitting,
  onCancel,
}: SOFormProps) {
  const { items, addItem, removeItem, updateItem, reset, orderTotal } =
    useSOLineItemsStore()

  React.useEffect(() => {
    return () => reset()
  }, [reset])

  const form = useForm<CreateSOFormValues>({
    resolver: zodResolver(createSOSchema),
    defaultValues: {
      order_number: "",
      customer: undefined,
      order_date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  })

  function handleFormSubmit(values: CreateSOFormValues) {
    const validLines = items.filter((item) => item.product !== null)

    if (validLines.length === 0) {
      toast.error("Add at least one line item")
      return
    }

    const hasInvalid = validLines.some(
      (item) => item.quantity < 1 || parseFloat(item.unitPrice) < 0,
    )
    if (hasInvalid) {
      toast.error("Fix line item errors before submitting")
      return
    }

    onSubmit({
      ...values,
      lines: validLines.map((item) => ({
        product: item.product!,
        quantity: item.quantity,
        unit_price: item.unitPrice,
      })),
    })
  }

  return (
    <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Order Details</CardTitle>
          <CardDescription>Basic information for the sales order.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <FormField
            label="Order Number"
            error={form.formState.errors.order_number?.message}
          >
            <Input
              placeholder="e.g. SO-2026-001"
              {...form.register("order_number")}
            />
          </FormField>

          <FormField
            label="Customer"
            error={form.formState.errors.customer?.message}
          >
            <Select
              value={form.watch("customer")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("customer", Number(val), { shouldValidate: true })
              }
              disabled={customersLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={customersLoading ? "Loading..." : "Select customer"}
                />
              </SelectTrigger>
              <SelectContent>
                {customers.map((c) => (
                  <SelectItem key={c.id} value={c.id.toString()}>
                    {c.code} — {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label="Order Date"
            error={form.formState.errors.order_date?.message}
          >
            <Input type="date" {...form.register("order_date")} />
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Line Items</CardTitle>
            <CardDescription>Add products to this order.</CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={addItem}>
            <PlusIcon className="mr-1 size-4" />
            Add Line
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[200px]">Product</TableHead>
                  <TableHead className="w-[120px]">Quantity</TableHead>
                  <TableHead className="w-[140px]">Unit Price</TableHead>
                  <TableHead className="w-[120px] text-right">Line Total</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.key}>
                    <TableCell>
                      <Select
                        value={item.product?.toString() ?? ""}
                        onValueChange={(val) => {
                          const p = products.find((pr) => pr.id === Number(val))
                          updateItem(item.key, {
                            product: Number(val),
                            productLabel: p ? `${p.sku} — ${p.name}` : "",
                          })
                        }}
                        disabled={productsLoading}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue
                            placeholder={productsLoading ? "Loading..." : "Select product"}
                          />
                        </SelectTrigger>
                        <SelectContent>
                          {products.map((p) => (
                            <SelectItem key={p.id} value={p.id.toString()}>
                              {p.sku} — {p.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        min={1}
                        value={item.quantity}
                        onChange={(e) =>
                          updateItem(item.key, {
                            quantity: Math.max(1, parseInt(e.target.value) || 1),
                          })
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={item.unitPrice}
                        onChange={(e) =>
                          updateItem(item.key, { unitPrice: e.target.value })
                        }
                      />
                    </TableCell>
                    <TableCell className="text-right tabular-nums font-medium">
                      {parseFloat(item.lineTotal).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="size-8"
                        onClick={() => removeItem(item.key)}
                        disabled={items.length <= 1}
                      >
                        <TrashIcon className="size-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={3} className="text-right font-semibold">
                    Order Total
                  </TableCell>
                  <TableCell className="text-right font-bold tabular-nums">
                    {parseFloat(orderTotal()).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableFooter>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Additional Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <FormField label="Notes" error={form.formState.errors.notes?.message}>
            <Textarea
              rows={3}
              placeholder="Internal notes, special instructions, etc."
              {...form.register("notes")}
            />
          </FormField>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Sales Order"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

function FormField({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
