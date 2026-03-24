"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { cn } from "@/lib/utils";
import {
  createCountLineSchema,
  type CountLineFormValues,
} from "../helpers/count-line-schemas";
import type { CycleCountLine } from "../types/cycle-count.types";

interface CountLineFormProps {
  lines: CycleCountLine[];
  onRecord: (
    lineId: number,
    product: number,
    location: number,
    countedQuantity: number,
    notes: string,
  ) => void;
  isRecording?: boolean;
}

export function CountLineForm({
  lines,
  onRecord,
  isRecording = false,
}: CountLineFormProps) {
  const t = useTranslations("CycleCounts.countLine");
  const tVal = useTranslations("CycleCounts.countLine.validation");
  const tCommon = useTranslations("Common.actions");

  const schema = useMemo(
    () =>
      createCountLineSchema({
        quantityInt: tVal("quantityInt"),
        quantityNonNegative: tVal("quantityNonNegative"),
      }),
    [tVal],
  );

  const [editingLine, setEditingLine] = useState<number | null>(null);

  const form = useForm<CountLineFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      quantity: 0,
      notes: "",
    },
  });

  function handleStartEdit(line: CycleCountLine) {
    setEditingLine(line.id);
    form.reset({
      quantity: line.counted_quantity ?? 0,
      notes: line.notes || "",
    });
  }

  function handleSubmit(line: CycleCountLine) {
    return form.handleSubmit((values) => {
      onRecord(
        line.id,
        line.product,
        line.location,
        values.quantity,
        values.notes ?? "",
      );
      setEditingLine(null);
      form.reset({ quantity: 0, notes: "" });
    });
  }

  function handleCancel() {
    setEditingLine(null);
    form.reset({ quantity: 0, notes: "" });
  }

  const uncountedLines = lines.filter((l) => l.counted_quantity === null);
  const countedLines = lines.filter((l) => l.counted_quantity !== null);

  return (
    <div className="space-y-4">
      {uncountedLines.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("pendingTitle")}</CardTitle>
            <CardDescription>
              {t("pendingRemaining", { count: uncountedLines.length })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {uncountedLines.map((line) => (
                <div key={line.id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{line.product_name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {line.product_sku}
                      </span>
                      <div className="text-sm text-muted-foreground">
                        {t("locationSystemLine", {
                          location: line.location_name,
                          systemQty: t("systemQty", {
                            qty: line.system_quantity,
                          }),
                        })}
                      </div>
                    </div>
                    {editingLine !== line.id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStartEdit(line)}
                      >
                        {t("recordCount")}
                      </Button>
                    )}
                  </div>

                  {editingLine === line.id && (
                    <Form {...form}>
                      <form
                        onSubmit={handleSubmit(line)}
                        className="mt-3 space-y-3 rounded-lg border p-3"
                      >
                        <div className="grid gap-3 sm:grid-cols-2">
                          <FormField
                            control={form.control}
                            name="quantity"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>{t("physicalCount")}</FormLabel>
                                <FormControl>
                                  <Input
                                    type="number"
                                    min={0}
                                    autoFocus
                                    value={field.value}
                                    onChange={(e) => {
                                      const n = parseInt(e.target.value, 10);
                                      field.onChange(
                                        Number.isNaN(n) ? 0 : n,
                                      );
                                    }}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="notes"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>{t("notes")}</FormLabel>
                                <FormControl>
                                  <Textarea
                                    rows={1}
                                    placeholder={t("notesPlaceholder")}
                                    {...field}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button
                            type="submit"
                            size="sm"
                            disabled={isRecording}
                          >
                            {isRecording ? t("saving") : t("save")}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={handleCancel}
                          >
                            {tCommon("cancel")}
                          </Button>
                        </div>
                      </form>
                    </Form>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {countedLines.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("countedTitle")}</CardTitle>
            <CardDescription>
              {t("countedSummary", { count: countedLines.length })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {countedLines.map((line) => {
                const variance = line.variance ?? 0;
                return (
                  <div
                    key={line.id}
                    className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                  >
                    <div>
                      <span className="font-medium">{line.product_name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {line.product_sku}
                      </span>
                      <div className="text-sm text-muted-foreground">
                        {line.location_name}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="text-muted-foreground">
                        {t("systemLabel")} {line.system_quantity}
                      </div>
                      <div>
                        {t("countedLabel")} {line.counted_quantity}
                      </div>
                      <div
                        className={cn(
                          "font-medium",
                          variance > 0 && "text-blue-600 dark:text-blue-400",
                          variance < 0 && "text-red-600 dark:text-red-400",
                          variance === 0 &&
                            "text-green-600 dark:text-green-400",
                        )}
                      >
                        {variance > 0 ? `+${variance}` : variance}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStartEdit(line)}
                      >
                        {t("recount")}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {lines.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {t("emptyLines")}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
