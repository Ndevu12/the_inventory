"use client";

import { use, useCallback, useEffect } from "react";
import { useRouter } from "@/i18n/navigation";
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
  const router = useRouter();

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
            toast.success("Count recorded");
          },
          onError: (error) => {
            toast.error(
              `Failed to record count: ${(error as { message?: string }).message ?? "Unknown error"}`,
            );
          },
        },
      );
    },
    [recordMutation],
  );

  const handleComplete = useCallback(() => {
    completeMutation.mutate(cycleId, {
      onSuccess: () => {
        toast.success("Cycle marked as completed");
        setStep("variances");
      },
      onError: (error) => {
        toast.error(
          `Failed to complete cycle: ${(error as { message?: string }).message ?? "Unknown error"}`,
        );
      },
    });
  }, [completeMutation, cycleId, setStep]);

  const handleReconcile = useCallback(() => {
    if (!cycle) return;

    const countedLines = cycle.lines.filter(
      (l) => l.counted_quantity !== null,
    );
    const payload: Record<string, { resolution: VarianceResolution; root_cause?: string }> = {};

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
          toast.success("Cycle reconciled successfully");
          reset();
        },
        onError: (error) => {
          toast.error(
            `Failed to reconcile: ${(error as { message?: string }).message ?? "Unknown error"}`,
          );
        },
      },
    );
  }, [cycle, resolutions, reconcileMutation, reset]);

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
        <PageHeader title="Cycle Not Found" />
        <p className="text-muted-foreground">
          The cycle count you are looking for does not exist.
        </p>
      </div>
    );
  }

  const isInProgress = cycle.status === "in_progress";
  const isCompleted = cycle.status === "completed";
  const isReconciled = cycle.status === "reconciled";
  const allCounted = cycle.lines.every((l) => l.counted_quantity !== null);

  return (
    <div className="space-y-6">
      <PageHeader
        title={cycle.name}
        description={`${cycle.location_name ?? "All Locations"} — Scheduled: ${new Date(cycle.scheduled_date).toLocaleDateString()}`}
        actions={
          <div className="flex items-center gap-2">
            <CycleStatusBadge status={cycle.status} />
            {isInProgress && allCounted && (
              <Button
                onClick={handleComplete}
                disabled={completeMutation.isPending}
              >
                <CheckCircle2Icon className="mr-2 size-4" />
                {completeMutation.isPending ? "Completing..." : "Mark Complete"}
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
            Count Lines ({cycle.counted_lines}/{cycle.total_lines})
          </TabsTrigger>
          <TabsTrigger value="variances" disabled={isInProgress}>
            Variances
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
