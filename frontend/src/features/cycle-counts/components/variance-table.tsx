"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
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
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DataTable } from "@/components/data-table";
import { cn } from "@/lib/utils";
import type {
  CycleCountLine,
  InventoryVariance,
  VarianceResolution,
  VarianceSummary,
} from "../types/cycle-count.types";
import { RESOLUTION_OPTIONS } from "../helpers/cycle-constants";
import { getVarianceColumns } from "./variance-columns";
import type { LineResolution } from "../stores/cycle-wizard-store";

interface VarianceReviewProps {
  lines: CycleCountLine[];
  variances: InventoryVariance[];
  summary: VarianceSummary;
  isReconciled: boolean;
  isCompleted: boolean;
  resolutions: Record<number, LineResolution>;
  onSetResolution: (lineId: number, resolution: LineResolution) => void;
  onBulkResolution: (lineIds: number[], resolution: VarianceResolution) => void;
  onReconcile: () => void;
  isReconciling?: boolean;
}

export function VarianceReview({
  lines,
  variances,
  summary,
  isReconciled,
  isCompleted,
  resolutions,
  onSetResolution,
  onBulkResolution,
  onReconcile,
  isReconciling = false,
}: VarianceReviewProps) {
  if (isReconciled && variances.length > 0) {
    return <ReconciledVarianceTable variances={variances} summary={summary} />;
  }

  const countedLines = lines.filter((l) => l.counted_quantity !== null);
  const linesWithVariance = countedLines.filter((l) => (l.variance ?? 0) !== 0);
  const linesWithMatch = countedLines.filter((l) => (l.variance ?? 0) === 0);

  const allNonZeroResolved = linesWithVariance.every(
    (l) => resolutions[l.id]?.resolution,
  );

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-4">
        <SummaryCard label="Total Lines" value={summary.total_lines} />
        <SummaryCard label="Shortages" value={summary.shortages} variant="destructive" />
        <SummaryCard label="Surpluses" value={summary.surpluses} variant="info" />
        <SummaryCard label="Matches" value={summary.matches} variant="success" />
      </div>

      {isCompleted && linesWithVariance.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resolve Variances</CardTitle>
            <CardDescription>
              {linesWithVariance.length} line{linesWithVariance.length !== 1 ? "s" : ""} with variances need resolution
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-3 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onBulkResolution(
                    linesWithVariance.map((l) => l.id),
                    "accepted",
                  )
                }
              >
                Accept All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onBulkResolution(
                    linesWithVariance.map((l) => l.id),
                    "investigating",
                  )
                }
              >
                Investigate All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onBulkResolution(
                    linesWithVariance.map((l) => l.id),
                    "rejected",
                  )
                }
              >
                Reject All
              </Button>
            </div>

            <div className="divide-y">
              {linesWithVariance.map((line) => {
                const variance = line.variance ?? 0;
                const res = resolutions[line.id];
                return (
                  <div key={line.id} className="space-y-2 py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium">{line.product_name}</span>
                        <span className="ml-2 text-xs text-muted-foreground">
                          {line.product_sku}
                        </span>
                        <span className="ml-2 text-sm text-muted-foreground">
                          @ {line.location_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-muted-foreground">
                          System: {line.system_quantity}
                        </span>
                        <span>Counted: {line.counted_quantity}</span>
                        <span
                          className={cn(
                            "font-semibold",
                            variance > 0 && "text-blue-600 dark:text-blue-400",
                            variance < 0 && "text-red-600 dark:text-red-400",
                          )}
                        >
                          {variance > 0 ? `+${variance}` : variance}
                        </span>
                      </div>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-1">
                        <Label className="text-xs">Resolution</Label>
                        <Select
                          value={res?.resolution ?? ""}
                          onValueChange={(val) =>
                            onSetResolution(line.id, {
                              resolution: val as VarianceResolution,
                              root_cause: res?.root_cause ?? "",
                            })
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select resolution..." />
                          </SelectTrigger>
                          <SelectContent>
                            {RESOLUTION_OPTIONS.map((opt) => (
                              <SelectItem key={opt.value} value={opt.value}>
                                {opt.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Root Cause</Label>
                        <Textarea
                          rows={1}
                          placeholder="Optional explanation..."
                          value={res?.root_cause ?? ""}
                          onChange={(e) =>
                            onSetResolution(line.id, {
                              resolution: res?.resolution ?? "investigating",
                              root_cause: e.target.value,
                            })
                          }
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button
              onClick={onReconcile}
              disabled={isReconciling || !allNonZeroResolved}
            >
              {isReconciling ? "Reconciling..." : "Reconcile Cycle"}
            </Button>
          </CardFooter>
        </Card>
      )}

      {isCompleted && linesWithMatch.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Matching Lines</CardTitle>
            <CardDescription>
              {linesWithMatch.length} line{linesWithMatch.length !== 1 ? "s" : ""} with no variance (auto-accepted)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y text-sm">
              {linesWithMatch.map((line) => (
                <div key={line.id} className="flex items-center justify-between py-2 first:pt-0 last:pb-0">
                  <div>
                    <span className="font-medium">{line.product_name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      @ {line.location_name}
                    </span>
                  </div>
                  <span className="text-green-600 dark:text-green-400">
                    Qty: {line.system_quantity} (match)
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!isCompleted && !isReconciled && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Complete all counts and mark the cycle as completed to review variances.
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ReconciledVarianceTable({
  variances,
  summary,
}: {
  variances: InventoryVariance[];
  summary: VarianceSummary;
}) {
  const columns = useMemo(() => getVarianceColumns(), []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-4">
        <SummaryCard label="Total Lines" value={summary.total_lines} />
        <SummaryCard label="Shortages" value={summary.shortages} variant="destructive" />
        <SummaryCard label="Surpluses" value={summary.surpluses} variant="info" />
        <SummaryCard label="Matches" value={summary.matches} variant="success" />
      </div>

      <DataTable
        columns={columns}
        data={variances}
        emptyMessage="No variances recorded."
      />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant?: "destructive" | "info" | "success";
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div
          className={cn(
            "text-2xl font-bold",
            variant === "destructive" && "text-red-600 dark:text-red-400",
            variant === "info" && "text-blue-600 dark:text-blue-400",
            variant === "success" && "text-green-600 dark:text-green-400",
          )}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
