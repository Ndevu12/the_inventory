"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { PlusIcon, Trash2Icon } from "lucide-react";
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
import { useBulkProducts, useBulkLocations, useBulkTransfer } from "../hooks/use-bulk";
import { useTransferItemsStore } from "../stores/bulk-items-store";
import {
  bulkTransferSchema,
  type BulkTransferFormValues,
} from "../helpers/bulk-schemas";
import { BulkResultSummary } from "./bulk-result-summary";
import type { BulkOperationResult, BulkTransferPayload } from "../api/bulk-api";

export function BulkTransferForm() {
  const [result, setResult] = React.useState<BulkOperationResult | null>(null);

  const { data: productsData, isLoading: productsLoading } = useBulkProducts();
  const { data: locationsData, isLoading: locationsLoading } = useBulkLocations();
  const transferMutation = useBulkTransfer();

  const products = productsData?.results ?? [];
  const locations = locationsData?.results ?? [];

  const { lines, addLine, removeLine, updateLine, reset: resetLines } =
    useTransferItemsStore();

  const form = useForm<BulkTransferFormValues>({
    resolver: zodResolver(bulkTransferSchema),
    defaultValues: {
      from_location: undefined as unknown as number,
      to_location: undefined as unknown as number,
      reference: "",
      notes: "",
    },
  });

  React.useEffect(() => {
    return () => resetLines();
  }, [resetLines]);

  function onSubmit(values: BulkTransferFormValues) {
    const validItems = lines.filter((l) => l.product_id && l.quantity > 0);
    if (validItems.length === 0) {
      toast.error("Add at least one product to transfer");
      return;
    }

    const payload: BulkTransferPayload = {
      items: validItems.map((l) => ({
        product_id: l.product_id!,
        quantity: l.quantity,
      })),
      from_location: values.from_location,
      to_location: values.to_location,
      reference: values.reference || undefined,
      notes: values.notes || undefined,
    };

    transferMutation.mutate(payload, {
      onSuccess: (data) => {
        setResult(data);
        if (data.failure_count === 0) {
          toast.success(`All ${data.total_count} items transferred successfully`);
        } else {
          toast.warning(
            `${data.success_count} of ${data.total_count} items transferred`,
          );
        }
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? "Bulk transfer failed";
        toast.error(message);
      },
    });
  }

  if (result) {
    return (
      <BulkResultSummary
        result={result}
        onReset={() => {
          setResult(null);
          form.reset();
          resetLines();
        }}
      />
    );
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Transfer Details</CardTitle>
          <CardDescription>
            Move stock from one location to another in bulk.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
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
                  placeholder={locationsLoading ? "Loading..." : "Select source"}
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
                  placeholder={
                    locationsLoading ? "Loading..." : "Select destination"
                  }
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

          <FormField
            label="Reference"
            error={form.formState.errors.reference?.message}
          >
            <Input
              placeholder="Optional reference number"
              {...form.register("reference")}
            />
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Products</CardTitle>
              <CardDescription>
                Add products and quantities to transfer.
              </CardDescription>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={addLine}>
              <PlusIcon className="mr-1 size-4" />
              Add Product
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="grid grid-cols-[1fr_120px_40px] gap-3 text-sm font-medium text-muted-foreground">
              <span>Product</span>
              <span>Quantity</span>
              <span />
            </div>
            {lines.map((line) => (
              <div
                key={line.id}
                className="grid grid-cols-[1fr_120px_40px] items-start gap-3"
              >
                <Select
                  value={line.product_id?.toString() ?? ""}
                  onValueChange={(val) =>
                    updateLine(line.id, { product_id: Number(val) })
                  }
                  disabled={productsLoading}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue
                      placeholder={
                        productsLoading ? "Loading..." : "Select product"
                      }
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
                <Input
                  type="number"
                  min={1}
                  value={line.quantity}
                  onChange={(e) =>
                    updateLine(line.id, {
                      quantity: parseInt(e.target.value) || 1,
                    })
                  }
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeLine(line.id)}
                  disabled={lines.length <= 1}
                >
                  <Trash2Icon className="size-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            rows={3}
            placeholder="Optional notes about this transfer..."
            {...form.register("notes")}
          />
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={transferMutation.isPending}>
          {transferMutation.isPending ? "Processing..." : "Execute Transfer"}
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
