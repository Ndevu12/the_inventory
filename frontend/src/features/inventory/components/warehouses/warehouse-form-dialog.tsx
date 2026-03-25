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
  useCreateWarehouse,
  useUpdateWarehouse,
} from "../../hooks/use-warehouses"
import {
  createWarehouseSchema,
  type WarehouseFormValues,
} from "../../helpers/warehouse-form-schema"
import type { Warehouse, WarehouseFormData } from "../../types/warehouse.types"

interface WarehouseFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  warehouse?: Warehouse | null
}

export function WarehouseFormDialog({
  open,
  onOpenChange,
  warehouse,
}: WarehouseFormDialogProps) {
  const t = useTranslations("Inventory")
  const tCommon = useTranslations("Common.actions")
  const isEditing = !!warehouse
  const createMutation = useCreateWarehouse()
  const updateMutation = useUpdateWarehouse()

  const schema = useMemo(
    () =>
      createWarehouseSchema({
        nameRequired: t("warehouses.form.validation.nameRequired"),
        nameMax: t("warehouses.form.validation.nameMax"),
        timezoneRequired: t("warehouses.form.validation.timezoneRequired"),
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
  } = useForm<WarehouseFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      description: "",
      is_active: true,
      timezone_name: "UTC",
      address: "",
    },
  })

  useEffect(() => {
    if (open) {
      reset({
        name: warehouse?.name ?? "",
        description: warehouse?.description ?? "",
        is_active: warehouse?.is_active ?? true,
        timezone_name: warehouse?.timezone_name ?? "UTC",
        address: warehouse?.address ?? "",
      })
    }
  }, [open, warehouse, reset])

  async function onSubmit(values: WarehouseFormValues) {
    const payload: WarehouseFormData = {
      name: values.name.trim(),
      description: values.description.trim(),
      is_active: values.is_active,
      timezone_name: values.timezone_name.trim(),
      address: values.address.trim(),
    }
    try {
      if (warehouse) {
        await updateMutation.mutateAsync({ id: warehouse.id, data: payload })
        toast.success(t("warehouses.toastUpdated", { name: payload.name }))
      } else {
        await createMutation.mutateAsync(payload)
        toast.success(t("warehouses.toastCreated", { name: payload.name }))
      }
      onOpenChange(false)
    } catch {
      toast.error(t("warehouses.toastSaveFailed"))
    }
  }

  const busy = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing
              ? t("warehouses.form.editTitle")
              : t("warehouses.form.createTitle")}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? t("warehouses.form.editDescription")
              : t("warehouses.form.createDescription")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="wh-name">{t("warehouses.form.name")}</Label>
            <Input
              id="wh-name"
              {...register("name")}
              placeholder={t("warehouses.form.namePlaceholder")}
            />
            {errors.name ? (
              <p className="text-destructive text-sm">{errors.name.message}</p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="wh-desc">{t("warehouses.form.description")}</Label>
            <Textarea
              id="wh-desc"
              {...register("description")}
              placeholder={t("warehouses.form.descriptionPlaceholder")}
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wh-tz">{t("warehouses.form.timezone")}</Label>
            <Input
              id="wh-tz"
              {...register("timezone_name")}
              placeholder={t("warehouses.form.timezonePlaceholder")}
            />
            {errors.timezone_name ? (
              <p className="text-destructive text-sm">
                {errors.timezone_name.message}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="wh-addr">{t("warehouses.form.address")}</Label>
            <Textarea
              id="wh-addr"
              {...register("address")}
              placeholder={t("warehouses.form.addressPlaceholder")}
              rows={2}
            />
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="wh-active"
              checked={watch("is_active")}
              onCheckedChange={(v) => setValue("is_active", v === true)}
            />
            <Label htmlFor="wh-active" className="font-normal">
              {t("warehouses.form.active")}
            </Label>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={busy}
            >
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={busy}>
              {busy
                ? t("warehouses.form.saving")
                : isEditing
                  ? t("warehouses.form.submitSave")
                  : t("warehouses.form.submitCreate")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
