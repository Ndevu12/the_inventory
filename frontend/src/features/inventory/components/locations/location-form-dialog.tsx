"use client"

import { useEffect, useMemo } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Link } from "@/i18n/navigation"
import { useCreateLocation, useUpdateLocation } from "../../hooks/use-locations"
import { useWarehousesForSelect } from "../../hooks/use-warehouses"
import {
  createLocationSchema,
  type LocationFormValues,
} from "../../helpers/location-form-schema"
import type { StockLocation, StockLocationFormData } from "../../types/location.types"

interface LocationFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  location?: StockLocation | null
}

export function LocationFormDialog({
  open,
  onOpenChange,
  location,
}: LocationFormDialogProps) {
  const t = useTranslations("Inventory")
  const tCommon = useTranslations("Common.actions")
  const isEditing = !!location
  const createMutation = useCreateLocation()
  const updateMutation = useUpdateLocation()

  const locationSchema = useMemo(
    () =>
      createLocationSchema({
        nameRequired: t("locations.form.validation.nameRequired"),
        nameMax: t("locations.form.validation.nameMax"),
      }),
    [t],
  )

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<LocationFormValues>({
    resolver: zodResolver(locationSchema),
    defaultValues: {
      name: "",
      description: "",
      is_active: true,
      max_capacity: "",
      warehouse_id: null,
    },
  })

  const { data: warehouses = [], isLoading: warehousesLoading } =
    useWarehousesForSelect()

  const facilitySelectItems = useMemo(
    () => [
      { value: "__none__", label: t("locations.form.noFacility") },
      ...warehouses.map((w) => ({ value: String(w.id), label: w.name })),
    ],
    [warehouses, t],
  )

  useEffect(() => {
    if (open) {
      reset({
        name: location?.name ?? "",
        description: location?.description ?? "",
        is_active: location?.is_active ?? true,
        max_capacity: location?.max_capacity?.toString() ?? "",
        warehouse_id: location?.warehouse_id ?? null,
      })
    }
  }, [open, location, reset])

  const isActive = watch("is_active")

  const onSubmit = (data: LocationFormValues) => {
    const payload: StockLocationFormData = {
      name: data.name,
      description: data.description,
      is_active: data.is_active,
      max_capacity: data.max_capacity ? Number(data.max_capacity) : null,
      warehouse_id: data.warehouse_id,
    }

    if (isEditing && location) {
      updateMutation.mutate(
        { id: location.id, data: payload },
        {
          onSuccess: () => {
            toast.success(t("locations.toastUpdated", { name: data.name }))
            onOpenChange(false)
          },
          onError: (err) =>
            toast.error(err.message || t("locations.toastUpdateFailed")),
        },
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          toast.success(t("locations.toastCreated", { name: data.name }))
          onOpenChange(false)
        },
        onError: (err) =>
          toast.error(err.message || t("locations.toastCreateFailed")),
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>
              {isEditing
                ? t("locations.form.editTitle")
                : t("locations.form.createTitle")}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? t("locations.form.editDescription")
                : t("locations.form.createDescription")}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="loc-facility">
                {t("locations.form.facility")}
              </Label>
              <Select
                items={facilitySelectItems}
                value={
                  watch("warehouse_id") != null
                    ? String(watch("warehouse_id")!)
                    : "__none__"
                }
                onValueChange={(val) =>
                  setValue(
                    "warehouse_id",
                    val === "__none__" ? null : Number(val),
                    { shouldValidate: true },
                  )
                }
                disabled={warehousesLoading}
              >
                <SelectTrigger id="loc-facility" className="w-full">
                  <SelectValue
                    placeholder={t("locations.form.facilityPlaceholder")}
                  />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">
                    {t("locations.form.noFacility")}
                  </SelectItem>
                  {warehouses.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>
                      {w.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t("locations.form.facilityHint")}
              </p>
              <Button variant="link" asChild className="h-auto p-0 text-xs font-normal">
                <Link href="/stock/warehouses">
                  {t("locations.noFacilitiesCalloutLink")}
                </Link>
              </Button>
            </div>

            <div className="space-y-2">
              <label htmlFor="loc-name" className="text-sm font-medium">
                {t("locations.form.name")}{" "}
                <span className="text-destructive">*</span>
              </label>
              <Input
                id="loc-name"
                placeholder={t("locations.form.namePlaceholder")}
                {...register("name")}
                aria-invalid={!!errors.name}
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="loc-desc" className="text-sm font-medium">
                {t("locations.form.description")}
              </label>
              <Textarea
                id="loc-desc"
                placeholder={t("locations.form.descriptionPlaceholder")}
                rows={3}
                {...register("description")}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="loc-capacity" className="text-sm font-medium">
                {t("locations.form.maxCapacity")}
              </label>
              <Input
                id="loc-capacity"
                type="number"
                min={1}
                placeholder={t("locations.form.capacityPlaceholder")}
                {...register("max_capacity")}
              />
              <p className="text-xs text-muted-foreground">
                {t("locations.form.capacityHint")}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="loc-active"
                checked={isActive}
                onCheckedChange={(checked) =>
                  setValue("is_active", Boolean(checked))
                }
              />
              <label
                htmlFor="loc-active"
                className="cursor-pointer text-sm font-medium"
              >
                {t("locations.form.active")}
              </label>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              disabled={isPending}
              onClick={() => onOpenChange(false)}
            >
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending
                ? t("locations.form.saving")
                : isEditing
                  ? t("locations.form.submitUpdate")
                  : t("locations.form.submitCreate")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
