"use client";

import { useCallback, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
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
import { RESERVATION_STATUS_VALUES } from "../helpers/reservation-constants";
import { ReservationTable } from "../components/reservation-table";
import type { StockReservation } from "../types/reservation.types";

export function ReservationListPage() {
  const router = useRouter();
  const filters = useReservationFiltersStore();
  const t = useTranslations("Reservations");
  const tStatus = useTranslations("Reservations.status");

  const STATUS_OPTIONS: FacetedFilterOption[] = useMemo(
    () =>
      RESERVATION_STATUS_VALUES.map((value) => ({
        value,
        label: tStatus(value),
      })),
    [tStatus],
  );

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

  const errMessage = useCallback(
    (error: unknown) =>
      (error as { message?: string }).message ?? t("errors.unknown"),
    [t],
  );

  const handleFulfill = useCallback(
    (reservation: StockReservation) => {
      fulfillMutation.mutate(reservation.id, {
        onSuccess: () => {
          toast.success(t("toast.fulfilled", { id: reservation.id }));
        },
        onError: (error) => {
          toast.error(
            t("toast.fulfillFailed", { message: errMessage(error) }),
          );
        },
      });
    },
    [fulfillMutation, t, errMessage],
  );

  const handleCancel = useCallback(
    (reservation: StockReservation) => {
      cancelMutation.mutate(reservation.id, {
        onSuccess: () => {
          toast.success(t("toast.cancelled", { id: reservation.id }));
        },
        onError: (error) => {
          toast.error(t("toast.cancelFailed", { message: errMessage(error) }));
        },
      });
    },
    [cancelMutation, t, errMessage],
  );

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("list.title")}
        description={t("list.description")}
        actions={
          <Button onClick={() => router.push("/reservations/new")}>
            <PlusIcon className="mr-2 size-4" />
            {t("list.newReservation")}
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
            title={t("list.filterStatus")}
            options={STATUS_OPTIONS}
          />
        }
      />
    </div>
  );
}
