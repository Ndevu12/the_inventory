"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
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
  buildCreateDispatchSchema,
  type CreateDispatchInput,
  type CreateDispatchFormValues,
} from "../../helpers/dispatch-schemas"
import type { SimpleSalesOrder, SimpleLocation } from "../../types/dispatch.types"

interface DispatchFormProps {
  salesOrders: SimpleSalesOrder[]
  salesOrdersLoading: boolean
  locations: SimpleLocation[]
  locationsLoading: boolean
  onSubmit: (values: CreateDispatchFormValues) => void
  isSubmitting: boolean
  onCancel: () => void
}

export function DispatchForm({
  salesOrders,
  salesOrdersLoading,
  locations,
  locationsLoading,
  onSubmit,
  isSubmitting,
  onCancel,
}: DispatchFormProps) {
  const t = useTranslations("Sales.dispatches.form")
  const tPh = useTranslations("Sales.dispatches.form.placeholders")
  const tVal = useTranslations("Sales.dispatches.validation")
  const tShared = useTranslations("Sales.shared")
  const tCommon = useTranslations("Common.actions")

  const dispatchSchema = React.useMemo(
    () =>
      buildCreateDispatchSchema({
        salesOrderRequired: tVal("salesOrderRequired"),
        dispatchDateRequired: tVal("dispatchDateRequired"),
        fromLocationRequired: tVal("fromLocationRequired"),
      }),
    [tVal],
  )

  const form = useForm<CreateDispatchInput, unknown, CreateDispatchFormValues>({
    resolver: zodResolver(dispatchSchema),
    defaultValues: {
      dispatch_number: "",
      sales_order: undefined as unknown as number,
      dispatch_date: new Date().toISOString().split("T")[0],
      from_location: undefined as unknown as number,
      notes: "",
    },
  })

  const sep = tShared("nameSeparator")

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("detailsTitle")}</CardTitle>
          <CardDescription>{t("detailsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <FormField
            label={t("dispatchNumberOptional")}
            error={form.formState.errors.dispatch_number?.message}
          >
            <Input
              placeholder={tPh("dispatchNumber")}
              {...form.register("dispatch_number")}
            />
          </FormField>

          <FormField
            label={t("salesOrder")}
            error={form.formState.errors.sales_order?.message}
          >
            <Select
              value={form.watch("sales_order")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("sales_order", Number(val), {
                  shouldValidate: true,
                })
              }
              disabled={salesOrdersLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={
                    salesOrdersLoading ? t("loading") : tPh("selectSalesOrder")
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {salesOrders.length === 0 ? (
                  <div className="px-2 py-3 text-sm text-muted-foreground">
                    {t("emptySalesOrdersHint")}
                  </div>
                ) : (
                  salesOrders.map((so) => (
                    <SelectItem key={so.id} value={so.id.toString()}>
                      {so.order_number}
                      {sep}
                      {so.customer_name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label={t("dispatchDate")}
            error={form.formState.errors.dispatch_date?.message}
          >
            <Input type="date" {...form.register("dispatch_date")} />
          </FormField>

          <FormField
            label={t("fromLocation")}
            error={form.formState.errors.from_location?.message}
          >
            <Select
              value={form.watch("from_location")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("from_location", Number(val), {
                  shouldValidate: true,
                })
              }
              disabled={locationsLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={
                    locationsLoading ? t("loading") : tPh("selectLocation")
                  }
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
          <CardTitle>{t("notesSectionTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <FormField
            label={t("notes")}
            error={form.formState.errors.notes?.message}
          >
            <Textarea
              rows={3}
              placeholder={tPh("notes")}
              {...form.register("notes")}
            />
          </FormField>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? t("creating") : t("submit")}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          {tCommon("cancel")}
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
