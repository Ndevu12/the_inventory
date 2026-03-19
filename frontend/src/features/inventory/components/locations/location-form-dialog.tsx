"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateLocation, useUpdateLocation } from "../../hooks/use-locations";
import type { StockLocation, StockLocationFormData } from "../../types/location.types";

const locationSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name is too long"),
  description: z.string(),
  is_active: z.boolean(),
  max_capacity: z.string(),
});

type FormValues = z.infer<typeof locationSchema>;

interface LocationFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  location?: StockLocation | null;
}

export function LocationFormDialog({
  open,
  onOpenChange,
  location,
}: LocationFormDialogProps) {
  const isEditing = !!location;
  const createMutation = useCreateLocation();
  const updateMutation = useUpdateLocation();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(locationSchema),
    defaultValues: {
      name: "",
      description: "",
      is_active: true,
      max_capacity: "",
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        name: location?.name ?? "",
        description: location?.description ?? "",
        is_active: location?.is_active ?? true,
        max_capacity: location?.max_capacity?.toString() ?? "",
      });
    }
  }, [open, location, reset]);

  const isActive = watch("is_active");

  const onSubmit = (data: FormValues) => {
    const payload: StockLocationFormData = {
      name: data.name,
      description: data.description,
      is_active: data.is_active,
      max_capacity: data.max_capacity ? Number(data.max_capacity) : null,
    };

    if (isEditing && location) {
      updateMutation.mutate(
        { id: location.id, data: payload },
        {
          onSuccess: () => {
            toast.success(`"${data.name}" updated`);
            onOpenChange(false);
          },
          onError: (err) =>
            toast.error(err.message || "Failed to update location"),
        },
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          toast.success(`"${data.name}" created`);
          onOpenChange(false);
        },
        onError: (err) =>
          toast.error(err.message || "Failed to create location"),
      });
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? "Edit Location" : "New Location"}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update the details for this stock location."
                : "Add a new stock location to your warehouse."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <label htmlFor="loc-name" className="text-sm font-medium">
                Name <span className="text-destructive">*</span>
              </label>
              <Input
                id="loc-name"
                placeholder="e.g. Warehouse A, Shelf B2"
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
                Description
              </label>
              <Textarea
                id="loc-desc"
                placeholder="Describe this location..."
                rows={3}
                {...register("description")}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="loc-capacity" className="text-sm font-medium">
                Max Capacity
              </label>
              <Input
                id="loc-capacity"
                type="number"
                min={1}
                placeholder="Leave empty for unlimited"
                {...register("max_capacity")}
              />
              <p className="text-xs text-muted-foreground">
                Maximum stock units this location can hold. Leave empty for
                unlimited capacity.
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
                Active
              </label>
            </div>
          </div>

          <DialogFooter>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Saving..." : isEditing ? "Update" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
