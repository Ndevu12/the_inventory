"use client";

import * as React from "react";
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
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useBulkProducts, useBulkRevalue } from "../hooks/use-bulk";
import { useRevalueItemsStore } from "../stores/bulk-items-store";
import { BulkResultSummary } from "./bulk-result-summary";
import type { BulkOperationResult, BulkRevaluePayload } from "../api/bulk-api";

export function BulkRevalueForm() {
  const [result, setResult] = React.useState<BulkOperationResult | null>(null);
  const tRevalue = useTranslations("BulkOperations.revalue");
  const tShared = useTranslations("BulkOperations.shared");

  const { data: productsData, isLoading: productsLoading } = useBulkProducts();
  const revalueMutation = useBulkRevalue();

  const products = productsData?.results ?? [];

  const { lines, addLine, removeLine, updateLine, reset: resetLines } =
    useRevalueItemsStore();

  React.useEffect(() => {
    return () => resetLines();
  }, [resetLines]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();

    const validItems = lines.filter(
      (l) =>
        l.product_id &&
        l.new_unit_cost !== "" &&
        !isNaN(Number(l.new_unit_cost)) &&
        Number(l.new_unit_cost) >= 0,
    );
    if (validItems.length === 0) {
      toast.error(tRevalue("toastNoItems"));
      return;
    }

    const payload: BulkRevaluePayload = {
      items: validItems.map((l) => ({
        product_id: l.product_id!,
        new_unit_cost: l.new_unit_cost,
      })),
    };

    revalueMutation.mutate(payload, {
      onSuccess: (data) => {
        setResult(data);
        if (data.failure_count === 0) {
          toast.success(
            tRevalue("toastAllSuccess", { count: data.total_count }),
          );
        } else {
          toast.warning(
            tRevalue("toastPartial", {
              success: data.success_count,
              total: data.total_count,
            }),
          );
        }
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? tRevalue("toastError");
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
          resetLines();
        }}
      />
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{tRevalue("cardTitle")}</CardTitle>
              <CardDescription>{tRevalue("cardDescription")}</CardDescription>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={addLine}>
              <PlusIcon className="mr-1 size-4" />
              {tShared("addProduct")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="grid grid-cols-[1fr_160px_40px] gap-3 text-sm font-medium text-muted-foreground">
              <span>{tShared("product")}</span>
              <span>{tShared("newUnitCost")}</span>
              <span />
            </div>
            {lines.map((line) => (
              <div
                key={line.id}
                className="grid grid-cols-[1fr_160px_40px] items-start gap-3"
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
                  type="text"
                  inputMode="decimal"
                  placeholder={tRevalue("unitCostPlaceholder")}
                  value={line.new_unit_cost}
                  onChange={(e) =>
                    updateLine(line.id, { new_unit_cost: e.target.value })
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

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={revalueMutation.isPending}>
          {revalueMutation.isPending
            ? tShared("processing")
            : tRevalue("execute")}
        </Button>
      </div>
    </form>
  );
}
