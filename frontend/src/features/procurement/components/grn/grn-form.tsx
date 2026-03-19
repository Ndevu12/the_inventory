"use client"

import type { UseFormReturn } from "react-hook-form"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { CreateGRNFormValues } from "../../helpers/grn-schemas"
import type { SimplePurchaseOrder, SimpleLocation } from "../../types/grn.types"

interface GRNFormProps {
  form: UseFormReturn<CreateGRNFormValues>
  purchaseOrders: SimplePurchaseOrder[]
  locations: SimpleLocation[]
  isLoadingPOs?: boolean
  isLoadingLocations?: boolean
}

export function GRNForm({
  form,
  purchaseOrders,
  locations,
  isLoadingPOs,
  isLoadingLocations,
}: GRNFormProps) {
  const {
    register,
    formState: { errors },
    setValue,
    watch,
  } = form

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>GRN Details</CardTitle>
          <CardDescription>
            Record goods received against a purchase order.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <FormField
            label="GRN Number"
            error={errors.grn_number?.message}
          >
            <Input
              placeholder="e.g. GRN-2026-001"
              {...register("grn_number")}
            />
          </FormField>

          <FormField
            label="Purchase Order"
            error={errors.purchase_order?.message}
          >
            <Select
              value={watch("purchase_order")?.toString() ?? ""}
              onValueChange={(val) =>
                setValue("purchase_order", Number(val), {
                  shouldValidate: true,
                })
              }
              disabled={isLoadingPOs}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={isLoadingPOs ? "Loading..." : "Select purchase order"}
                />
              </SelectTrigger>
              <SelectContent>
                {purchaseOrders.map((po) => (
                  <SelectItem key={po.id} value={po.id.toString()}>
                    {po.order_number} — {po.supplier_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label="Received Date"
            error={errors.received_date?.message}
          >
            <Input type="date" {...register("received_date")} />
          </FormField>

          <FormField
            label="Location"
            error={errors.location?.message}
          >
            <Select
              value={watch("location")?.toString() ?? ""}
              onValueChange={(val) =>
                setValue("location", Number(val), {
                  shouldValidate: true,
                })
              }
              disabled={isLoadingLocations}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={isLoadingLocations ? "Loading..." : "Select location"}
                />
              </SelectTrigger>
              <SelectContent>
                {locations.map((loc) => (
                  <SelectItem key={loc.id} value={loc.id.toString()}>
                    {loc.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Additional Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <FormField label="Notes" error={errors.notes?.message}>
            <Textarea
              rows={3}
              placeholder="Condition of goods, discrepancies, etc."
              {...register("notes")}
            />
          </FormField>
        </CardContent>
      </Card>
    </>
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
