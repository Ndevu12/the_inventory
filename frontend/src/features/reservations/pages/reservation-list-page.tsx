"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import type { PaginationState } from "@tanstack/react-table";
import { PlusIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import {
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table/data-table-faceted-filter";

import {
  useReservations,
  useFulfillReservation,
  useCancelReservation,
} from "../hooks/use-reservations";
import { useReservationFiltersStore } from "../stores/reservation-filters-store";
import { RESERVATION_STATUSES } from "../helpers/reservation-constants";
import { ReservationTable } from "../components/reservation-table";
import type { StockReservation } from "../types/reservation.types";

const STATUS_OPTIONS: FacetedFilterOption[] = RESERVATION_STATUSES.map((s) => ({
  label: s.label,
  value: s.value,
}));

export function ReservationListPage() {
  const router = useRouter();
  const filters = useReservationFiltersStore();

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: filters.pageSize,
  });

  const { data, isLoading } = useReservations({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    ordering: "-created_at",
    search: filters.search || undefined,
    status: filters.status || undefined,
  });

  const fulfillMutation = useFulfillReservation();
  const cancelMutation = useCancelReservation();

  const handleFulfill = useCallback(
    (reservation: StockReservation) => {
      fulfillMutation.mutate(reservation.id, {
        onSuccess: () => {
          toast.success(`Reservation #${reservation.id} fulfilled`);
        },
        onError: (error) => {
          toast.error(
            `Failed to fulfill: ${(error as { message?: string }).message ?? "Unknown error"}`,
          );
        },
      });
    },
    [fulfillMutation],
  );

  const handleCancel = useCallback(
    (reservation: StockReservation) => {
      cancelMutation.mutate(reservation.id, {
        onSuccess: () => {
          toast.success(`Reservation #${reservation.id} cancelled`);
        },
        onError: (error) => {
          toast.error(
            `Failed to cancel: ${(error as { message?: string }).message ?? "Unknown error"}`,
          );
        },
      });
    },
    [cancelMutation],
  );

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reservations"
        description="Manage stock reservations for sales orders and manual holds."
        actions={
          <Button onClick={() => router.push("/reservations/new")}>
            <PlusIcon className="mr-2 size-4" />
            New Reservation
          </Button>
        }
      />

      <ReservationTable
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={filters.search}
        onSearchChange={filters.setSearch}
        onFulfill={handleFulfill}
        onCancel={handleCancel}
        isLoading={isLoading}
        filterContent={
          <DataTableFacetedFilter
            title="Status"
            options={STATUS_OPTIONS}
          />
        }
      />
    </div>
  );
}
