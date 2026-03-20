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
  createReservationSchema,
  type CreateReservationFormValues,
} from "../helpers/reservation-schemas";
import type { CreateReservationPayload } from "../types/reservation.types";

interface ProductOption {
  id: number;
  name: string;
  sku: string;
}

interface LocationOption {
  id: number;
  name: string;
}

interface SalesOrderOption {
  id: number;
  order_number: string;
}

interface ReservationFormProps {
  products: ProductOption[];
  locations: LocationOption[];
  salesOrders: SalesOrderOption[];
  onSubmit: (values: CreateReservationPayload) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function ReservationForm({
  products,
  locations,
  salesOrders,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: ReservationFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateReservationFormValues>({
    resolver: zodResolver(createReservationSchema),
    defaultValues: {
      quantity: "1",
      notes: "",
      sales_order: "",
    },
  });

  function handleFormSubmit(values: CreateReservationFormValues) {
    const qty = parseInt(values.quantity, 10);
    if (isNaN(qty) || qty < 1) return;
    onSubmit({
      product: Number(values.product),
      location: Number(values.location),
      quantity: qty,
      sales_order: values.sales_order ? Number(values.sales_order) : null,
      notes: values.notes,
    });
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <Card>
        <CardHeader>
          <CardTitle>New Reservation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Product *</Label>
              <Select
                value={watch("product")?.toString() ?? ""}
                onValueChange={(val) =>
                  setValue("product", val as string, { shouldValidate: true })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a product..." />
                </SelectTrigger>
                <SelectContent>
                  {products.map((p) => (
                    <SelectItem key={p.id} value={p.id.toString()}>
                      {p.sku} — {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.product && (
                <p className="text-xs text-destructive">
                  {errors.product.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Location *</Label>
              <Select
                value={watch("location")?.toString() ?? ""}
                onValueChange={(val) =>
                  setValue("location", val as string, { shouldValidate: true })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a location..." />
                </SelectTrigger>
                <SelectContent>
                  {locations.map((l) => (
                    <SelectItem key={l.id} value={l.id.toString()}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.location && (
                <p className="text-xs text-destructive">
                  {errors.location.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="quantity">Quantity *</Label>
              <Input
                id="quantity"
                type="number"
                min={1}
                {...register("quantity")}
              />
              {errors.quantity && (
                <p className="text-xs text-destructive">
                  {errors.quantity.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Sales Order (optional)</Label>
              <Select
                value={watch("sales_order") || ""}
                onValueChange={(val) =>
                  setValue("sales_order", (val === "__none__" ? "" : val) as string, {
                    shouldValidate: true,
                  })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">None</SelectItem>
                  {salesOrders.map((so) => (
                    <SelectItem key={so.id} value={so.id.toString()}>
                      {so.order_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.sales_order && (
                <p className="text-xs text-destructive">
                  {errors.sales_order.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Textarea
              id="notes"
              rows={3}
              placeholder="Any additional notes..."
              {...register("notes")}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create Reservation"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
