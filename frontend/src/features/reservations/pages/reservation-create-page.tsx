"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useAllProducts } from "@/features/inventory/hooks/use-products";
import { useAllLocations } from "@/features/inventory/hooks/use-locations";
import { useAllSalesOrders } from "@/features/sales/hooks/use-sales-orders";

import { useCreateReservation } from "../hooks/use-reservations";
import { ReservationForm } from "../components/reservation-form";
import type { CreateReservationPayload } from "../types/reservation.types";

export function ReservationCreatePage() {
  const router = useRouter();
  const createMutation = useCreateReservation();
  const { data: products, isLoading: productsLoading } = useAllProducts();
  const { data: locations, isLoading: locationsLoading } = useAllLocations();
  const { data: salesOrders, isLoading: salesOrdersLoading } = useAllSalesOrders();

  const isLoading = productsLoading || locationsLoading || salesOrdersLoading;

  function handleSubmit(values: CreateReservationPayload) {
    createMutation.mutate(values,
      {
        onSuccess: () => {
          toast.success("Reservation created successfully");
          router.push("/reservations");
        },
        onError: (error) => {
          toast.error(
            `Failed to create reservation: ${(error as { message?: string }).message ?? "Unknown error"}`,
          );
        },
      },
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Reservation"
        description="Reserve stock for a sales order or manual hold."
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : (
        <ReservationForm
          products={products ?? []}
          locations={locations ?? []}
          salesOrders={salesOrders ?? []}
          onSubmit={handleSubmit}
          onCancel={() => router.push("/reservations")}
          isSubmitting={createMutation.isPending}
        />
      )}
    </div>
  );
}
