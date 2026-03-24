"use client";

import { useRouter } from "@/i18n/navigation";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api-common";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";

import { useStartCycle } from "../hooks/use-cycles";
import { CycleForm } from "../components/cycle-form";
import type { CycleCreatePayload } from "../types/cycle-count.types";

interface Location {
  id: number;
  name: string;
}

function useLocations() {
  return useQuery({
    queryKey: ["stock-locations", "all"],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Location>>("/stock-locations/", {
        page_size: "1000",
      }),
    select: (data) => data.results,
  });
}

export function CycleCreatePage() {
  const router = useRouter();
  const startMutation = useStartCycle();
  const { data: locations, isLoading: locationsLoading } = useLocations();

  function handleSubmit(values: CycleCreatePayload) {
    startMutation.mutate(values, {
      onSuccess: (cycle) => {
        toast.success("Cycle count started successfully");
        router.push(`/cycle-counts/${cycle.id}`);
      },
      onError: (error) => {
        toast.error(
          `Failed to start cycle: ${(error as { message?: string }).message ?? "Unknown error"}`,
        );
      },
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Start Cycle Count"
        description="Create a new physical inventory count cycle."
      />

      {locationsLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : (
        <CycleForm
          locations={locations ?? []}
          onSubmit={handleSubmit}
          onCancel={() => router.push("/cycle-counts")}
          isSubmitting={startMutation.isPending}
        />
      )}
    </div>
  );
}
