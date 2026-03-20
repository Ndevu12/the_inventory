"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  createCycleSchema,
  type CreateCycleFormValues,
} from "../helpers/cycle-schemas";
import type { CycleCreatePayload } from "../types/cycle-count.types";

interface LocationOption {
  id: number;
  name: string;
}

interface CycleFormProps {
  locations: LocationOption[];
  onSubmit: (values: CycleCreatePayload) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function CycleForm({
  locations,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: CycleFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateCycleFormValues>({
    resolver: zodResolver(createCycleSchema),
    defaultValues: {
      name: "",
      location: "",
      scheduled_date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  });

  function handleFormSubmit(values: CreateCycleFormValues) {
    onSubmit({
      name: values.name,
      location: values.location ? Number(values.location) : null,
      scheduled_date: values.scheduled_date,
      notes: values.notes,
    });
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <Card>
        <CardHeader>
          <CardTitle>New Cycle Count</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Q1 2026 Full Count"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Location (optional)</Label>
              <Select
                value={watch("location") || ""}
                onValueChange={(val) => {
                  if (val) {
                    const locationValue = val === "__all__" ? "" : val;
                    setValue("location", locationValue, {
                      shouldValidate: true,
                    });
                  }
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All Locations (Full Warehouse)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">
                    All Locations (Full Warehouse)
                  </SelectItem>
                  {locations.map((l) => (
                    <SelectItem key={l.id} value={l.id.toString()}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="scheduled_date">Scheduled Date *</Label>
              <Input
                id="scheduled_date"
                type="date"
                {...register("scheduled_date")}
              />
              {errors.scheduled_date && (
                <p className="text-xs text-destructive">
                  {errors.scheduled_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Textarea
              id="notes"
              rows={3}
              placeholder="Any additional notes about this cycle count..."
              {...register("notes")}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Starting..." : "Start Cycle Count"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
