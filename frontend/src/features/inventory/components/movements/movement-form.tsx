"use client"

import * as React from "react"
import { useRouter } from "@/i18n/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
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
import { useCreateMovement, useProducts, useLocations } from "../../hooks/use-movements"
import { useMovementFormStore } from "../../stores/movement-form-store"
import {
  createMovementFormSchema,
  type MovementFormValues,
  MOVEMENT_TYPE_VALUES,
  ALLOCATION_STRATEGY_VALUES,
  showFromLocation,
  showToLocation,
  showLotFields,
  showAllocationStrategy,
} from "../../helpers/movement-schemas"
import type { MovementType, StockMovementCreatePayload } from "../../api/movements-api"

export function MovementForm() {
  const router = useRouter()
  const inv = useTranslations("Inventory")
  const tCommon = useTranslations("Common.actions")
  const tStates = useTranslations("Common.states")
  const { movementType, setMovementType, enableLotFields, setEnableLotFields, reset: resetStore } =
    useMovementFormStore()

  const movementFormSchema = React.useMemo(
    () =>
      createMovementFormSchema({
        productRequired: inv("movements.form.validation.productRequired"),
        quantityMin: inv("movements.form.validation.quantityMin"),
        receiveToRequired: inv("movements.form.validation.receiveToRequired"),
        issueFromRequired: inv("movements.form.validation.issueFromRequired"),
        transferFromRequired: inv(
          "movements.form.validation.transferFromRequired",
        ),
        transferToRequired: inv("movements.form.validation.transferToRequired"),
        transferLocationsDiffer: inv(
          "movements.form.validation.transferLocationsDiffer",
        ),
        adjustmentLocationRequired: inv(
          "movements.form.validation.adjustmentLocationRequired",
        ),
      }),
    [inv],
  )

  const { data: productsData, isLoading: productsLoading } = useProducts()
  const { data: locationsData, isLoading: locationsLoading } = useLocations()
  const createMovement = useCreateMovement()

  const products = productsData?.results ?? []
  const locations = locationsData?.results ?? []

  const form = useForm<MovementFormValues>({
    resolver: zodResolver(movementFormSchema),
    defaultValues: {
      product: undefined,
      movement_type: "receive",
      quantity: 1,
      from_location: undefined,
      to_location: undefined,
      unit_cost: "",
      reference: "",
      notes: "",
      lot_number: "",
      serial_number: "",
      manufacturing_date: "",
      expiry_date: "",
      allocation_strategy: "FIFO",
    },
  })

  const watchedType = form.watch("movement_type")

  React.useEffect(() => {
    if (watchedType && watchedType !== movementType) {
      setMovementType(watchedType)
      form.setValue("from_location", undefined)
      form.setValue("to_location", undefined)
      if (watchedType !== "receive") {
        setEnableLotFields(false)
        form.setValue("lot_number", "")
        form.setValue("serial_number", "")
        form.setValue("manufacturing_date", "")
        form.setValue("expiry_date", "")
      }
    }
  }, [watchedType, movementType, setMovementType, setEnableLotFields, form])

  React.useEffect(() => {
    return () => resetStore()
  }, [resetStore])

  function onSubmit(values: MovementFormValues) {
    const payload: StockMovementCreatePayload = {
      product: values.product,
      movement_type: values.movement_type,
      quantity: values.quantity,
    }

    if (values.from_location) payload.from_location = values.from_location
    if (values.to_location) payload.to_location = values.to_location
    if (values.unit_cost) payload.unit_cost = values.unit_cost
    if (values.reference) payload.reference = values.reference
    if (values.notes) payload.notes = values.notes

    if (enableLotFields && showLotFields(values.movement_type)) {
      if (values.lot_number) payload.lot_number = values.lot_number
      if (values.serial_number) payload.serial_number = values.serial_number
      if (values.manufacturing_date)
        payload.manufacturing_date = values.manufacturing_date
      if (values.expiry_date) payload.expiry_date = values.expiry_date
    }

    if (showAllocationStrategy(values.movement_type) && values.allocation_strategy) {
      payload.allocation_strategy = values.allocation_strategy
    }

    createMovement.mutate(payload, {
      onSuccess: () => {
        toast.success(inv("movements.form.toastSuccess"))
        router.push("/stock/movements")
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ??
          inv("movements.form.toastError")
        toast.error(message)
      },
    })
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{inv("movements.form.cardMovement")}</CardTitle>
          <CardDescription>
            {inv("movements.form.cardMovementHint")}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <FormField
            label={inv("movements.form.labels.movementType")}
            error={form.formState.errors.movement_type?.message}
          >
            <Select
              value={form.watch("movement_type")}
              onValueChange={(val) =>
                form.setValue("movement_type", val as MovementType, {
                  shouldValidate: true,
                })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={inv("movements.form.placeholders.selectType")} />
              </SelectTrigger>
              <SelectContent>
                {MOVEMENT_TYPE_VALUES.map((mt) => (
                  <SelectItem key={mt} value={mt}>
                    {inv(`movementTypes.${mt}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label={inv("movements.form.labels.product")}
            error={form.formState.errors.product?.message}
          >
            <Select
              value={form.watch("product")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("product", Number(val), { shouldValidate: true })
              }
              disabled={productsLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={
                    productsLoading
                      ? tStates("loading")
                      : inv("movements.form.placeholders.selectProduct")
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id.toString()}>
                    {p.sku}
                    {inv("shared.nameSeparator")}
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label={inv("movements.form.labels.quantity")}
            error={form.formState.errors.quantity?.message}
          >
            <Input
              type="number"
              min={1}
              {...form.register("quantity", { valueAsNumber: true })}
            />
          </FormField>

          <FormField
            label={inv("movements.form.labels.unitCost")}
            error={form.formState.errors.unit_cost?.message}
          >
            <Input
              type="text"
              inputMode="decimal"
              placeholder="0.00"
              {...form.register("unit_cost")}
            />
          </FormField>

          {showFromLocation(movementType) && (
            <FormField
              label={inv("movements.form.labels.sourceLocation")}
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
                      locationsLoading
                        ? tStates("loading")
                        : inv("movements.form.placeholders.selectLocation")
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {locations.map((l) => (
                    <SelectItem key={l.id} value={l.id.toString()}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          )}

          {showToLocation(movementType) && (
            <FormField
              label={inv("movements.form.labels.destinationLocation")}
              error={form.formState.errors.to_location?.message}
            >
              <Select
                value={form.watch("to_location")?.toString() ?? ""}
                onValueChange={(val) =>
                  form.setValue("to_location", Number(val), {
                    shouldValidate: true,
                  })
                }
                disabled={locationsLoading}
              >
                <SelectTrigger className="w-full">
                  <SelectValue
                    placeholder={
                      locationsLoading
                        ? tStates("loading")
                        : inv("movements.form.placeholders.selectLocation")
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {locations.map((l) => (
                    <SelectItem key={l.id} value={l.id.toString()}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          )}

          <FormField
            label={inv("movements.form.labels.reference")}
            error={form.formState.errors.reference?.message}
          >
            <Input
              placeholder={inv("movements.form.placeholders.reference")}
              {...form.register("reference")}
            />
          </FormField>
        </CardContent>
      </Card>

      {showLotFields(movementType) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <CardTitle>{inv("movements.form.cardLot")}</CardTitle>
                <CardDescription>
                  {inv("movements.form.cardLotHint")}
                </CardDescription>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEnableLotFields(!enableLotFields)}
              >
                {enableLotFields
                  ? inv("movements.form.removeLot")
                  : inv("movements.form.addLot")}
              </Button>
            </div>
          </CardHeader>
          {enableLotFields && (
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <FormField
                label={inv("movements.form.labels.lotNumber")}
                error={form.formState.errors.lot_number?.message}
              >
                <Input
                  placeholder={inv("movements.form.placeholders.lotNumber")}
                  {...form.register("lot_number")}
                />
              </FormField>

              <FormField
                label={inv("movements.form.labels.serialNumber")}
                error={form.formState.errors.serial_number?.message}
              >
                <Input
                  placeholder={inv("movements.form.placeholders.serial")}
                  {...form.register("serial_number")}
                />
              </FormField>

              <FormField
                label={inv("movements.form.labels.manufacturingDate")}
                error={form.formState.errors.manufacturing_date?.message}
              >
                <Input type="date" {...form.register("manufacturing_date")} />
              </FormField>

              <FormField
                label={inv("movements.form.labels.expiryDate")}
                error={form.formState.errors.expiry_date?.message}
              >
                <Input type="date" {...form.register("expiry_date")} />
              </FormField>
            </CardContent>
          )}
        </Card>
      )}

      {showAllocationStrategy(movementType) && (
        <Card>
          <CardHeader>
            <CardTitle>{inv("movements.form.cardAllocation")}</CardTitle>
            <CardDescription>
              {inv("movements.form.cardAllocationHint")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FormField
              label={inv("movements.form.labels.strategy")}
              error={form.formState.errors.allocation_strategy?.message}
            >
              <Select
                value={form.watch("allocation_strategy") ?? "FIFO"}
                onValueChange={(val) =>
                  form.setValue(
                    "allocation_strategy",
                    val as "FIFO" | "LIFO",
                    { shouldValidate: true },
                  )
                }
              >
                <SelectTrigger className="w-full sm:w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALLOCATION_STRATEGY_VALUES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {inv(`allocationStrategies.${s}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{inv("movements.form.cardNotes")}</CardTitle>
        </CardHeader>
        <CardContent>
          <FormField
            label={inv("movements.form.labels.notes")}
            error={form.formState.errors.notes?.message}
          >
            <Textarea
              rows={3}
              placeholder={inv("movements.form.placeholders.notes")}
              {...form.register("notes")}
            />
          </FormField>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={createMovement.isPending}>
          {createMovement.isPending
            ? inv("movements.form.submitting")
            : inv("movements.form.submit")}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push("/stock/movements")}
        >
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
