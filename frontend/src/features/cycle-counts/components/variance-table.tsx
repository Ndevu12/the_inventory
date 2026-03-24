"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
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
import { VARIANCE_RESOLUTION_VALUES } from "../helpers/cycle-constants";
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
  onBulkResolution: (
    lineIds: number[],
    resolution: VarianceResolution,
  ) => void;
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
  const t = useTranslations("CycleCounts.variance");

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
        <SummaryCard label={t("summaryTotalLines")} value={summary.total_lines} />
        <SummaryCard
          label={t("summaryShortages")}
          value={summary.shortages}
          variant="destructive"
        />
        <SummaryCard
          label={t("summarySurpluses")}
          value={summary.surpluses}
          variant="info"
        />
        <SummaryCard
          label={t("summaryMatches")}
          value={summary.matches}
          variant="success"
        />
      </div>

      {isCompleted && linesWithVariance.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("resolveTitle")}</CardTitle>
            <CardDescription>
              {t("resolveNeedCount", { count: linesWithVariance.length })}
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
                {t("acceptAll")}
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
                {t("investigateAll")}
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
                {t("rejectAll")}
              </Button>
            </div>

            <div className="divide-y">
              {linesWithVariance.map((line) => {
                const variance = line.variance ?? 0;
                const res = resolutions[line.id];
                return (
                  <div
                    key={line.id}
                    className="space-y-2 py-3 first:pt-0 last:pb-0"
                  >
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
                          {t("inlineSystem", { qty: line.system_quantity })}
                        </span>
                        <span>
                          {t("inlineCounted", {
                            qty: line.counted_quantity ?? "",
                          })}
                        </span>
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
                        <Label className="text-xs">{t("resolution")}</Label>
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
                            <SelectValue placeholder={t("resolutionPlaceholder")} />
                          </SelectTrigger>
                          <SelectContent>
                            {VARIANCE_RESOLUTION_VALUES.map((opt) => (
                              <SelectItem key={opt} value={opt}>
                                {t(`resolutionOption.${opt}`)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">{t("rootCause")}</Label>
                        <Textarea
                          rows={1}
                          placeholder={t("rootCausePlaceholder")}
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
              {isReconciling ? t("reconciling") : t("reconcile")}
            </Button>
          </CardFooter>
        </Card>
      )}

      {isCompleted && linesWithMatch.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("matchingTitle")}</CardTitle>
            <CardDescription>
              {t("matchingNoVariance", { count: linesWithMatch.length })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y text-sm">
              {linesWithMatch.map((line) => (
                <div
                  key={line.id}
                  className="flex items-center justify-between py-2 first:pt-0 last:pb-0"
                >
                  <div>
                    <span className="font-medium">{line.product_name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      @ {line.location_name}
                    </span>
                  </div>
                  <span className="text-green-600 dark:text-green-400">
                    {t("qtyMatch", { qty: line.system_quantity })}
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
            {t("completeToReview")}
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
  const t = useTranslations("CycleCounts.variance");
  const tCol = useTranslations("CycleCounts.varianceTable");
  const tType = useTranslations("CycleCounts.variance.type");
  const tRes = useTranslations("CycleCounts.variance.resolutionOption");

  const columns = useMemo(
    () => getVarianceColumns(tCol, tType, tRes),
    [tCol, tType, tRes],
  );

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-4">
        <SummaryCard label={t("summaryTotalLines")} value={summary.total_lines} />
        <SummaryCard
          label={t("summaryShortages")}
          value={summary.shortages}
          variant="destructive"
        />
        <SummaryCard
          label={t("summarySurpluses")}
          value={summary.surpluses}
          variant="info"
        />
        <SummaryCard
          label={t("summaryMatches")}
          value={summary.matches}
          variant="success"
        />
      </div>

      <DataTable
        columns={columns}
        data={variances}
        emptyMessage={t("emptyVariances")}
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
