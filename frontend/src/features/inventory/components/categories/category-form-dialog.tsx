"use client"

import { useEffect, useMemo } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import {
  createCategorySchema,
  type CategoryFormValues,
} from "../../helpers/category-schemas"
import type { Category } from "../../types/inventory.types"

interface CategoryFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: Category | null
  onSubmit: (values: CategoryFormValues) => void
  isSubmitting: boolean
}

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  onSubmit,
  isSubmitting,
}: CategoryFormDialogProps) {
  const t = useTranslations("Inventory")
  const tCommon = useTranslations("Common.actions")
  const isEdit = !!category

  const categorySchema = useMemo(
    () =>
      createCategorySchema({
        nameRequired: t("categories.form.validation.nameRequired"),
        nameMax: t("categories.form.validation.nameMax"),
        slugMax: t("categories.form.validation.slugMax"),
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
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: "",
      slug: "",
      description: "",
      is_active: true,
    },
  })

  useEffect(() => {
    if (open) {
      reset(
        category
          ? {
              name: category.name,
              slug: category.slug,
              description: category.description,
              is_active: category.is_active,
            }
          : { name: "", slug: "", description: "", is_active: true },
      )
    }
  }, [open, category, reset])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit
              ? t("categories.form.editTitle")
              : t("categories.form.createTitle")}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? t("categories.form.editDescription")
              : t("categories.form.createDescription")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="cat-name" className="text-sm font-medium">
              {t("categories.form.name")}{" "}
              <span className="text-destructive">*</span>
            </label>
            <Input
              id="cat-name"
              placeholder={t("categories.form.namePlaceholder")}
              {...register("name")}
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p className="text-xs text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="cat-slug" className="text-sm font-medium">
              {t("categories.form.slug")}
            </label>
            <Input
              id="cat-slug"
              placeholder={t("categories.form.slugPlaceholder")}
              {...register("slug")}
              aria-invalid={!!errors.slug}
            />
            {errors.slug && (
              <p className="text-xs text-destructive">
                {errors.slug.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {t("categories.form.slugHint")}
            </p>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="cat-desc" className="text-sm font-medium">
              {t("categories.form.description")}
            </label>
            <Textarea
              id="cat-desc"
              placeholder={t("categories.form.descriptionPlaceholder")}
              rows={3}
              {...register("description")}
            />
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="cat-active"
              checked={watch("is_active")}
              onCheckedChange={(checked: boolean) =>
                setValue("is_active", checked)
              }
            />
            <label htmlFor="cat-active" className="text-sm">
              {t("categories.form.active")}
            </label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? t("categories.form.saving")
                : isEdit
                  ? t("categories.form.updateSubmit")
                  : t("categories.form.createSubmit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
