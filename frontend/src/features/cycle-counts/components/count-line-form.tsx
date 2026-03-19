"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
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
  countLineSchema,
  type CountLineFormValues,
} from "../helpers/count-line-schemas";
import type { CycleCountLine } from "../types/cycle-count.types";

interface CountLineFormProps {
  lines: CycleCountLine[];
  onRecord: (lineId: number, product: number, location: number, countedQuantity: number, notes: string) => void;
  isRecording?: boolean;
}

export function CountLineForm({
  lines,
  onRecord,
  isRecording = false,
}: CountLineFormProps) {
  const [editingLine, setEditingLine] = useState<number | null>(null);

  const form = useForm<CountLineFormValues>({
    resolver: zodResolver(countLineSchema),
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
      onRecord(line.id, line.product, line.location, values.quantity, values.notes ?? "");
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
            <CardTitle className="text-base">Pending Counts</CardTitle>
            <CardDescription>
              {uncountedLines.length} item{uncountedLines.length !== 1 ? "s" : ""} remaining
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
                        {line.location_name} — System qty: {line.system_quantity}
                      </div>
                    </div>
                    {editingLine !== line.id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStartEdit(line)}
                      >
                        Record Count
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
                                <FormLabel>Physical Count *</FormLabel>
                                <FormControl>
                                  <Input
                                    type="number"
                                    min={0}
                                    {...field}
                                    autoFocus
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
                                <FormLabel>Notes</FormLabel>
                                <FormControl>
                                  <Textarea
                                    rows={1}
                                    placeholder="Optional notes..."
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
                            {isRecording ? "Saving..." : "Save"}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={handleCancel}
                          >
                            Cancel
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
            <CardTitle className="text-base">Counted</CardTitle>
            <CardDescription>
              {countedLines.length} item{countedLines.length !== 1 ? "s" : ""} counted
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {countedLines.map((line) => {
                const variance = line.variance ?? 0;
                return (
                  <div key={line.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
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
                        System: {line.system_quantity}
                      </div>
                      <div>
                        Counted: {line.counted_quantity}
                      </div>
                      <div
                        className={cn(
                          "font-medium",
                          variance > 0 && "text-blue-600 dark:text-blue-400",
                          variance < 0 && "text-red-600 dark:text-red-400",
                          variance === 0 && "text-green-600 dark:text-green-400",
                        )}
                      >
                        {variance > 0 ? `+${variance}` : variance}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStartEdit(line)}
                      >
                        Recount
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
            No count lines found for this cycle.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
