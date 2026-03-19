"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  categorySchema,
  type CategoryFormValues,
} from "../../helpers/category-schemas";
import type { Category } from "../../types/inventory.types";

interface CategoryFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  category: Category | null;
  onSubmit: (values: CategoryFormValues) => void;
  isSubmitting: boolean;
}

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  onSubmit,
  isSubmitting,
}: CategoryFormDialogProps) {
  const isEdit = !!category;

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
  });

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
      );
    }
  }, [open, category, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit Category" : "Create Category"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the category details below."
              : "Fill in the details to create a new category."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="cat-name" className="text-sm font-medium">
              Name <span className="text-destructive">*</span>
            </label>
            <Input
              id="cat-name"
              placeholder="e.g. Electronics"
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
              Slug
            </label>
            <Input
              id="cat-slug"
              placeholder="auto-generated if empty"
              {...register("slug")}
              aria-invalid={!!errors.slug}
            />
            {errors.slug && (
              <p className="text-xs text-destructive">
                {errors.slug.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              URL-friendly identifier. Leave blank to auto-generate from the
              name.
            </p>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="cat-desc" className="text-sm font-medium">
              Description
            </label>
            <Textarea
              id="cat-desc"
              placeholder="Optional description..."
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
              Active
            </label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? "Saving…"
                : isEdit
                  ? "Update Category"
                  : "Create Category"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
