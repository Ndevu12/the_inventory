"use client"

import { useMemo } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { Loader2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
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
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  createProductSchema,
  type ProductSchemaValues,
} from "../../helpers/product-schemas"
import {
  UNIT_OF_MEASURE_VALUES,
  TRACKING_MODE_VALUES,
} from "../../helpers/inventory-constants"
import type { Product, Category } from "../../types/inventory.types"

interface ProductFormProps {
  initialData?: Product
  categories: Category[]
  onSubmit: (data: ProductSchemaValues) => void
  isSubmitting?: boolean
}

function toDefaults(product?: Product): ProductSchemaValues {
  if (!product) {
    return {
      sku: "",
      name: "",
      description: "",
      category: null,
      unit_of_measure: "pcs",
      unit_cost: 0,
      reorder_point: 0,
      tracking_mode: "none",
      is_active: true,
    }
  }
  return {
    sku: product.sku,
    name: product.name,
    description: product.description,
    category: product.category,
    unit_of_measure: product.unit_of_measure,
    unit_cost: parseFloat(product.unit_cost),
    reorder_point: product.reorder_point,
    tracking_mode: "none",
    is_active: product.is_active,
  }
}

export function ProductForm({
  initialData,
  categories,
  onSubmit,
  isSubmitting = false,
}: ProductFormProps) {
  const t = useTranslations("Inventory")

  const productSchema = useMemo(
    () =>
      createProductSchema({
        skuRequired: t("products.form.validation.skuRequired"),
        skuMax: t("products.form.validation.skuMax"),
        nameRequired: t("products.form.validation.nameRequired"),
        nameMax: t("products.form.validation.nameMax"),
        unitOfMeasureRequired: t(
          "products.form.validation.unitOfMeasureRequired",
        ),
        unitCostMin: t("products.form.validation.unitCostMin"),
        reorderPointInt: t("products.form.validation.reorderPointInt"),
        reorderPointMin: t("products.form.validation.reorderPointMin"),
      }),
    [t],
  )

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ProductSchemaValues>({
    resolver: zodResolver(productSchema),
    defaultValues: toDefaults(initialData),
  })

  const unitOfMeasure = watch("unit_of_measure")
  const trackingMode = watch("tracking_mode")
  const isActive = watch("is_active")
  const categoryValue = watch("category")

  const categorySelectItems = useMemo(
    () => [
      { value: "__none__", label: t("products.form.noCategory") },
      ...categories.map((cat) => ({
        value: String(cat.id),
        label: cat.name,
      })),
    ],
    [categories, t],
  )

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("products.form.basicInfo")}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="sku">{t("products.form.labels.sku")}</Label>
            <Input
              id="sku"
              placeholder={t("products.form.placeholders.sku")}
              {...register("sku")}
            />
            {errors.sku && (
              <p className="text-sm text-destructive">{errors.sku.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">{t("products.form.labels.name")}</Label>
            <Input
              id="name"
              placeholder={t("products.form.placeholders.name")}
              {...register("name")}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="description">
              {t("products.form.labels.description")}
            </Label>
            <Textarea
              id="description"
              placeholder={t("products.form.placeholders.description")}
              rows={3}
              {...register("description")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">
              {t("products.form.labels.category")}
            </Label>
            <Select
              items={categorySelectItems}
              value={
                categoryValue != null ? String(categoryValue) : "__none__"
              }
              onValueChange={(val) =>
                setValue(
                  "category",
                  val === "__none__" ? null : Number(val),
                  { shouldValidate: true },
                )
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={t("products.form.selectCategory")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">
                  {t("products.form.noCategory")}
                </SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={String(cat.id)}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("products.form.inventorySettings")}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="unit_of_measure">
              {t("products.form.labels.unitOfMeasure")}
            </Label>
            <Select
              value={unitOfMeasure}
              onValueChange={(val) => {
                if (val) setValue("unit_of_measure", val, { shouldValidate: true })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {UNIT_OF_MEASURE_VALUES.map((uom) => (
                  <SelectItem key={uom} value={uom}>
                    {t(`units.${uom}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="unit_cost">
              {t("products.form.labels.unitCost")}
            </Label>
            <Input
              id="unit_cost"
              type="number"
              step="0.01"
              min="0"
              placeholder={t("products.form.placeholders.unitCost")}
              {...register("unit_cost", { valueAsNumber: true })}
            />
            {errors.unit_cost && (
              <p className="text-sm text-destructive">
                {errors.unit_cost.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="reorder_point">
              {t("products.form.labels.reorderPoint")}
            </Label>
            <Input
              id="reorder_point"
              type="number"
              min="0"
              step="1"
              placeholder={t("products.form.placeholders.reorderPoint")}
              {...register("reorder_point", { valueAsNumber: true })}
            />
            {errors.reorder_point && (
              <p className="text-sm text-destructive">
                {errors.reorder_point.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="tracking_mode">
              {t("products.form.labels.trackingMode")}
            </Label>
            <Select
              value={trackingMode}
              onValueChange={(val) => {
                if (val) setValue("tracking_mode", val, { shouldValidate: true })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TRACKING_MODE_VALUES.map((mode) => (
                  <SelectItem key={mode} value={mode}>
                    {t(`trackingModes.${mode}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-3 sm:col-span-2">
            <Switch
              checked={isActive}
              onCheckedChange={(checked) =>
                setValue("is_active", Boolean(checked), {
                  shouldValidate: true,
                })
              }
            />
            <Label htmlFor="is_active">{t("products.form.labels.active")}</Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2Icon className="mr-2 size-4 animate-spin" />}
          {initialData
            ? t("products.form.submitSave")
            : t("products.form.submitCreate")}
        </Button>
      </div>
    </form>
  )
}
