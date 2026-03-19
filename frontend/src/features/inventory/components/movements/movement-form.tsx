"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateMovement, useProducts, useLocations } from "../../hooks/use-movements";
import { useMovementFormStore } from "../../stores/movement-form-store";
import {
  movementFormSchema,
  type MovementFormValues,
  MOVEMENT_TYPES,
  ALLOCATION_STRATEGIES,
  showFromLocation,
  showToLocation,
  showLotFields,
  showAllocationStrategy,
} from "../../helpers/movement-schemas";
import type { MovementType, StockMovementCreatePayload } from "../../api/movements-api";

export function MovementForm() {
  const router = useRouter();
  const { movementType, setMovementType, enableLotFields, setEnableLotFields, reset: resetStore } =
    useMovementFormStore();

  const { data: productsData, isLoading: productsLoading } = useProducts();
  const { data: locationsData, isLoading: locationsLoading } = useLocations();
  const createMovement = useCreateMovement();

  const products = productsData?.results ?? [];
  const locations = locationsData?.results ?? [];

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
  });

  const watchedType = form.watch("movement_type");

  React.useEffect(() => {
    if (watchedType && watchedType !== movementType) {
      setMovementType(watchedType);
      form.setValue("from_location", undefined);
      form.setValue("to_location", undefined);
      if (watchedType !== "receive") {
        setEnableLotFields(false);
        form.setValue("lot_number", "");
        form.setValue("serial_number", "");
        form.setValue("manufacturing_date", "");
        form.setValue("expiry_date", "");
      }
    }
  }, [watchedType, movementType, setMovementType, setEnableLotFields, form]);

  React.useEffect(() => {
    return () => resetStore();
  }, [resetStore]);

  function onSubmit(values: MovementFormValues) {
    const payload: StockMovementCreatePayload = {
      product: values.product,
      movement_type: values.movement_type,
      quantity: values.quantity,
    };

    if (values.from_location) payload.from_location = values.from_location;
    if (values.to_location) payload.to_location = values.to_location;
    if (values.unit_cost) payload.unit_cost = values.unit_cost;
    if (values.reference) payload.reference = values.reference;
    if (values.notes) payload.notes = values.notes;

    if (enableLotFields && showLotFields(values.movement_type)) {
      if (values.lot_number) payload.lot_number = values.lot_number;
      if (values.serial_number) payload.serial_number = values.serial_number;
      if (values.manufacturing_date)
        payload.manufacturing_date = values.manufacturing_date;
      if (values.expiry_date) payload.expiry_date = values.expiry_date;
    }

    if (showAllocationStrategy(values.movement_type) && values.allocation_strategy) {
      payload.allocation_strategy = values.allocation_strategy;
    }

    createMovement.mutate(payload, {
      onSuccess: () => {
        toast.success("Movement created successfully");
        router.push("/stock/movements");
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? "Failed to create movement";
        toast.error(message);
      },
    });
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {/* Core fields */}
      <Card>
        <CardHeader>
          <CardTitle>Movement Details</CardTitle>
          <CardDescription>
            Select the type, product, quantity, and relevant locations.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <FormField label="Movement Type" error={form.formState.errors.movement_type?.message}>
            <Select
              value={form.watch("movement_type")}
              onValueChange={(val) =>
                form.setValue("movement_type", val as MovementType, {
                  shouldValidate: true,
                })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {MOVEMENT_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField label="Product" error={form.formState.errors.product?.message}>
            <Select
              value={form.watch("product")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("product", Number(val), { shouldValidate: true })
              }
              disabled={productsLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={productsLoading ? "Loading..." : "Select product"}
                />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id.toString()}>
                    {p.sku} — {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField label="Quantity" error={form.formState.errors.quantity?.message}>
            <Input
              type="number"
              min={1}
              {...form.register("quantity", { valueAsNumber: true })}
            />
          </FormField>

          <FormField label="Unit Cost" error={form.formState.errors.unit_cost?.message}>
            <Input
              type="text"
              inputMode="decimal"
              placeholder="0.00"
              {...form.register("unit_cost")}
            />
          </FormField>

          {showFromLocation(movementType) && (
            <FormField
              label="Source Location"
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
                    placeholder={locationsLoading ? "Loading..." : "Select location"}
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
              label="Destination Location"
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
                    placeholder={locationsLoading ? "Loading..." : "Select location"}
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

          <FormField label="Reference" error={form.formState.errors.reference?.message}>
            <Input
              placeholder="PO number, SO number, etc."
              {...form.register("reference")}
            />
          </FormField>
        </CardContent>
      </Card>

      {/* Lot fields — only for receive movements */}
      {showLotFields(movementType) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <CardTitle>Lot / Batch Information</CardTitle>
                <CardDescription>
                  Optionally assign this received stock to a lot.
                </CardDescription>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEnableLotFields(!enableLotFields)}
              >
                {enableLotFields ? "Remove Lot" : "Add Lot"}
              </Button>
            </div>
          </CardHeader>
          {enableLotFields && (
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <FormField label="Lot Number" error={form.formState.errors.lot_number?.message}>
                <Input
                  placeholder="e.g. BATCH-2026-001"
                  {...form.register("lot_number")}
                />
              </FormField>

              <FormField
                label="Serial Number"
                error={form.formState.errors.serial_number?.message}
              >
                <Input
                  placeholder="Optional serial"
                  {...form.register("serial_number")}
                />
              </FormField>

              <FormField
                label="Manufacturing Date"
                error={form.formState.errors.manufacturing_date?.message}
              >
                <Input type="date" {...form.register("manufacturing_date")} />
              </FormField>

              <FormField
                label="Expiry Date"
                error={form.formState.errors.expiry_date?.message}
              >
                <Input type="date" {...form.register("expiry_date")} />
              </FormField>
            </CardContent>
          )}
        </Card>
      )}

      {/* Allocation strategy — for issue and transfer */}
      {showAllocationStrategy(movementType) && (
        <Card>
          <CardHeader>
            <CardTitle>Lot Allocation Strategy</CardTitle>
            <CardDescription>
              Choose how lots are allocated when issuing or transferring stock.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FormField
              label="Strategy"
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
                  {ALLOCATION_STRATEGIES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <FormField label="Notes" error={form.formState.errors.notes?.message}>
            <Textarea
              rows={3}
              placeholder="Optional notes about this movement..."
              {...form.register("notes")}
            />
          </FormField>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button type="submit" disabled={createMovement.isPending}>
          {createMovement.isPending ? "Creating..." : "Create Movement"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push("/stock/movements")}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}

function FormField({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
