"use client"

import { useRouter } from "@/i18n/navigation"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { DispatchForm } from "../components/dispatches/dispatch-form"
import {
  useCreateDispatch,
  useDispatchSalesOrders,
  useDispatchLocations,
} from "../hooks/use-dispatches"
import type { CreateDispatchFormValues } from "../helpers/dispatch-schemas"

export function DispatchCreatePage() {
  const router = useRouter()
  const createMutation = useCreateDispatch()
  const { data: soData, isLoading: sosLoading } = useDispatchSalesOrders()
  const { data: locData, isLoading: locsLoading } = useDispatchLocations()

  const salesOrders = soData?.results ?? []
  const locations = locData?.results ?? []

  function handleSubmit(values: CreateDispatchFormValues) {
    createMutation.mutate(values, {
      onSuccess: (dispatch) => {
        toast.success(`Dispatch "${dispatch.dispatch_number}" created`)
        router.push("/sales/dispatches")
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ??
          "Failed to create dispatch"
        toast.error(message)
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="New Dispatch"
        description="Create a dispatch to ship goods against a sales order"
      />
      <DispatchForm
        salesOrders={salesOrders}
        salesOrdersLoading={sosLoading}
        locations={locations}
        locationsLoading={locsLoading}
        onSubmit={handleSubmit}
        isSubmitting={createMutation.isPending}
        onCancel={() => router.push("/sales/dispatches")}
      />
    </div>
  )
}
