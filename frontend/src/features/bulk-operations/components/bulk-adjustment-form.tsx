"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
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
import {
  useBulkProducts,
  useBulkLocations,
  useBulkAdjustment,
} from "../hooks/use-bulk";
import { useAdjustmentItemsStore } from "../stores/bulk-items-store";
import {
  createBulkAdjustmentSchema,
  type BulkAdjustmentFormValues,
} from "../helpers/bulk-schemas";
import { BulkResultSummary } from "./bulk-result-summary";
import type { BulkOperationResult, BulkAdjustmentPayload } from "../api/bulk-api";

export function BulkAdjustmentForm() {
  const [result, setResult] = React.useState<BulkOperationResult | null>(null);
  const tAdjust = useTranslations("BulkOperations.adjustment");
  const tVal = useTranslations("BulkOperations.validation");
  const tShared = useTranslations("BulkOperations.shared");

  const schema = React.useMemo(
    () =>
      createBulkAdjustmentSchema({
        locationRequired: tVal("locationRequired"),
      }),
    [tVal],
  );

  const { data: productsData, isLoading: productsLoading } = useBulkProducts();
  const { data: locationsData, isLoading: locationsLoading } = useBulkLocations();
  const adjustMutation = useBulkAdjustment();

  const products = productsData?.results ?? [];
  const locations = locationsData?.results ?? [];

  const { lines, addLine, removeLine, updateLine, reset: resetLines } =
    useAdjustmentItemsStore();

  const form = useForm<BulkAdjustmentFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      location: undefined as unknown as number,
      notes: "",
    },
  });

  React.useEffect(() => {
    return () => resetLines();
  }, [resetLines]);

  function onSubmit(values: BulkAdjustmentFormValues) {
    const validItems = lines.filter(
      (l) => l.product_id && l.new_quantity >= 0,
    );
    if (validItems.length === 0) {
      toast.error(tAdjust("toastNoItems"));
      return;
    }

    const payload: BulkAdjustmentPayload = {
      items: validItems.map((l) => ({
        product_id: l.product_id!,
        new_quantity: l.new_quantity,
      })),
      location: values.location,
      notes: values.notes || undefined,
    };

    adjustMutation.mutate(payload, {
      onSuccess: (data) => {
        setResult(data);
        if (data.failure_count === 0) {
          toast.success(
            tAdjust("toastAllSuccess", { count: data.total_count }),
          );
        } else {
          toast.warning(
            tAdjust("toastPartial", {
              success: data.success_count,
              total: data.total_count,
            }),
          );
        }
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? tAdjust("toastError");
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
          <CardTitle>{tAdjust("cardTitle")}</CardTitle>
          <CardDescription>{tAdjust("cardDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <FormField
            label={tAdjust("location")}
            error={form.formState.errors.location?.message}
          >
            <Select
              value={form.watch("location")?.toString() ?? ""}
              onValueChange={(val) =>
                form.setValue("location", Number(val), {
                  shouldValidate: true,
                })
              }
              disabled={locationsLoading}
            >
              <SelectTrigger className="w-full sm:w-80">
                <SelectValue
                  placeholder={
                    locationsLoading
                      ? tShared("loading")
                      : tShared("selectLocation")
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{tAdjust("productsTitle")}</CardTitle>
              <CardDescription>
                {tAdjust("productsDescription")}
              </CardDescription>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={addLine}>
              <PlusIcon className="mr-1 size-4" />
              {tShared("addProduct")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="grid grid-cols-[1fr_140px_40px] gap-3 text-sm font-medium text-muted-foreground">
              <span>{tShared("product")}</span>
              <span>{tShared("newQuantity")}</span>
              <span />
            </div>
            {lines.map((line) => (
              <div
                key={line.id}
                className="grid grid-cols-[1fr_140px_40px] items-start gap-3"
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
                        productsLoading
                          ? tShared("loading")
                          : tShared("selectProduct")
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
                  min={0}
                  value={line.new_quantity}
                  onChange={(e) =>
                    updateLine(line.id, {
                      new_quantity: parseInt(e.target.value) || 0,
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
          <CardTitle>{tShared("notes")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            rows={3}
            placeholder={tAdjust("notesPlaceholder")}
            {...form.register("notes")}
          />
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={adjustMutation.isPending}>
          {adjustMutation.isPending
            ? tShared("processing")
            : tAdjust("execute")}
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
