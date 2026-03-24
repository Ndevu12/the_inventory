"use client"

import { useRouter } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import type { ApiError } from "@/types/api-common"
import { DispatchForm } from "../components/dispatches/dispatch-form"
import {
  useCreateDispatch,
  useDispatchSalesOrders,
  useDispatchLocations,
} from "../hooks/use-dispatches"
import type { CreateDispatchFormValues } from "../helpers/dispatch-schemas"
import type { DispatchCreatePayload } from "../types/dispatch.types"

export function DispatchCreatePage() {
  const router = useRouter()
  const t = useTranslations("Sales.dispatches.create")
  const createMutation = useCreateDispatch()
  const { data: soData, isLoading: sosLoading } = useDispatchSalesOrders()
  const { data: locData, isLoading: locsLoading } = useDispatchLocations()

  const salesOrders = soData?.results ?? []
  const locations = locData?.results ?? []

  function handleSubmit(values: CreateDispatchFormValues) {
    const { dispatch_number, ...rest } = values
    const trimmed = dispatch_number.trim()
    const payload: DispatchCreatePayload = {
      ...rest,
      ...(trimmed ? { dispatch_number: trimmed } : {}),
    }
    createMutation.mutate(payload, {
      onSuccess: (dispatch) => {
        toast.success(
          t("toastCreated", { dispatchNumber: dispatch.dispatch_number }),
        )
        router.push("/sales/dispatches")
      },
      onError: (error: unknown) => {
        const e = error as unknown as ApiError
        toast.error(e.message || t("toastCreateFailed"))
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />
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
