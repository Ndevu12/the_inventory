"use client";

import { use, useCallback, useEffect } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2Icon, ClipboardCheckIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import {
  useCycle,
  useRecordCount,
  useCompleteCycle,
  useReconcileCycle,
} from "../hooks/use-cycles";
import { useCycleWizardStore } from "../stores/cycle-wizard-store";
import { CycleStatusBadge } from "../components/cycle-status-badge";
import { CountLineForm } from "../components/count-line-form";
import { VarianceReview } from "../components/variance-table";
import type { VarianceResolution } from "../types/cycle-count.types";

interface CycleDetailPageProps {
  params: Promise<{ id: string }>;
}

export function CycleDetailPage({ params }: CycleDetailPageProps) {
  const { id } = use(params);
  const cycleId = Number(id);
  const t = useTranslations("CycleCounts");

  const { data: cycle, isLoading } = useCycle(cycleId);
  const recordMutation = useRecordCount(cycleId);
  const completeMutation = useCompleteCycle();
  const reconcileMutation = useReconcileCycle(cycleId);

  const {
    step,
    resolutions,
    setStep,
    setResolution,
    setBulkResolution,
    reset,
  } = useCycleWizardStore();

  useEffect(() => {
    return () => reset();
  }, [reset]);

  useEffect(() => {
    if (!cycle) return;
    if (cycle.status === "reconciled") setStep("variances");
    else if (cycle.status === "completed") setStep("variances");
    else setStep("count");
  }, [cycle?.status, setStep, cycle]);

  const errMessage = useCallback(
    (error: unknown) =>
      (error as { message?: string }).message ?? t("errors.unknown"),
    [t],
  );

  const handleRecordCount = useCallback(
    (
      _lineId: number,
      product: number,
      location: number,
      countedQuantity: number,
      notes: string,
    ) => {
      recordMutation.mutate(
        { product, location, counted_quantity: countedQuantity, notes },
        {
          onSuccess: () => {
            toast.success(t("toast.recordSuccess"));
          },
          onError: (error) => {
            toast.error(
              t("toast.recordFailed", { message: errMessage(error) }),
            );
          },
        },
      );
    },
    [recordMutation, t, errMessage],
  );

  const handleComplete = useCallback(() => {
    completeMutation.mutate(cycleId, {
      onSuccess: () => {
        toast.success(t("toast.completeSuccess"));
        setStep("variances");
      },
      onError: (error) => {
        toast.error(
          t("toast.completeFailed", { message: errMessage(error) }),
        );
      },
    });
  }, [completeMutation, cycleId, setStep, t, errMessage]);

  const handleReconcile = useCallback(() => {
    if (!cycle) return;

    const countedLines = cycle.lines.filter(
      (l) => l.counted_quantity !== null,
    );
    const payload: Record<
      string,
      { resolution: VarianceResolution; root_cause?: string }
    > = {};

    for (const line of countedLines) {
      const variance = line.variance ?? 0;
      if (variance !== 0) {
        const res = resolutions[line.id];
        if (!res?.resolution) continue;
        payload[String(line.id)] = {
          resolution: res.resolution,
          root_cause: res.root_cause || undefined,
        };
      }
    }

    reconcileMutation.mutate(
      { resolutions: payload },
      {
        onSuccess: () => {
          toast.success(t("toast.reconcileSuccess"));
          reset();
        },
        onError: (error) => {
          toast.error(
            t("toast.reconcileFailed", { message: errMessage(error) }),
          );
        },
      },
    );
  }, [cycle, resolutions, reconcileMutation, reset, t, errMessage]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!cycle) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("notFound.title")} />
        <p className="text-muted-foreground">{t("notFound.body")}</p>
      </div>
    );
  }

  const isInProgress = cycle.status === "in_progress";
  const isCompleted = cycle.status === "completed";
  const isReconciled = cycle.status === "reconciled";
  const allCounted = cycle.lines.every((l) => l.counted_quantity !== null);

  const scheduledDate = new Date(cycle.scheduled_date).toLocaleDateString();

  return (
    <div className="space-y-6">
      <PageHeader
        title={cycle.name}
        description={t("detail.description", {
          location: cycle.location_name ?? t("detail.allLocations"),
          scheduled: t("detail.scheduled"),
          date: scheduledDate,
        })}
        actions={
          <div className="flex items-center gap-2">
            <CycleStatusBadge status={cycle.status} />
            {isInProgress && allCounted && (
              <Button
                onClick={handleComplete}
                disabled={completeMutation.isPending}
              >
                <CheckCircle2Icon className="mr-2 size-4" />
                {completeMutation.isPending
                  ? t("detail.completing")
                  : t("detail.markComplete")}
              </Button>
            )}
          </div>
        }
      />

      <Tabs
        value={step}
        onValueChange={(v) => setStep(v as "count" | "variances")}
      >
        <TabsList>
          <TabsTrigger value="count" disabled={isReconciled}>
            <ClipboardCheckIcon className="mr-2 size-4" />
            {t("tabs.countLines", {
              counted: cycle.counted_lines,
              total: cycle.total_lines,
            })}
          </TabsTrigger>
          <TabsTrigger value="variances" disabled={isInProgress}>
            {t("tabs.variances")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="count" className="mt-4">
          <CountLineForm
            lines={cycle.lines}
            onRecord={handleRecordCount}
            isRecording={recordMutation.isPending}
          />
        </TabsContent>

        <TabsContent value="variances" className="mt-4">
          <VarianceReview
            lines={cycle.lines}
            variances={cycle.variances}
            summary={cycle.variance_summary}
            isReconciled={isReconciled}
            isCompleted={isCompleted}
            resolutions={resolutions}
            onSetResolution={setResolution}
            onBulkResolution={setBulkResolution}
            onReconcile={handleReconcile}
            isReconciling={reconcileMutation.isPending}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
