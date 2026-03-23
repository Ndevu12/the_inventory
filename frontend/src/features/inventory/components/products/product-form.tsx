"use client"

import { useMemo } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
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

import { productSchema, type ProductSchemaValues } from "../../helpers/product-schemas"
import { UNITS_OF_MEASURE, TRACKING_MODES } from "../../helpers/inventory-constants"
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
      { value: "__none__", label: "No category" },
      ...categories.map((cat) => ({
        value: String(cat.id),
        label: cat.name,
      })),
    ],
    [categories],
  )

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="sku">SKU</Label>
            <Input
              id="sku"
              placeholder="e.g. PHONE-001"
              {...register("sku")}
            />
            {errors.sku && (
              <p className="text-sm text-destructive">{errors.sku.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="e.g. iPhone 15 Pro"
              {...register("name")}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Optional product description"
              rows={3}
              {...register("description")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
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
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">No category</SelectItem>
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
          <CardTitle>Inventory Settings</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="unit_of_measure">Unit of Measure</Label>
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
                {UNITS_OF_MEASURE.map((uom) => (
                  <SelectItem key={uom.value} value={uom.value}>
                    {uom.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="unit_cost">Unit Cost</Label>
            <Input
              id="unit_cost"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              {...register("unit_cost", { valueAsNumber: true })}
            />
            {errors.unit_cost && (
              <p className="text-sm text-destructive">
                {errors.unit_cost.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="reorder_point">Reorder Point</Label>
            <Input
              id="reorder_point"
              type="number"
              min="0"
              step="1"
              placeholder="0"
              {...register("reorder_point", { valueAsNumber: true })}
            />
            {errors.reorder_point && (
              <p className="text-sm text-destructive">
                {errors.reorder_point.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="tracking_mode">Tracking Mode</Label>
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
                {TRACKING_MODES.map((mode) => (
                  <SelectItem key={mode.value} value={mode.value}>
                    {mode.label}
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
            <Label htmlFor="is_active">Active</Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2Icon className="mr-2 size-4 animate-spin" />}
          {initialData ? "Save Changes" : "Create Product"}
        </Button>
      </div>
    </form>
  )
}
