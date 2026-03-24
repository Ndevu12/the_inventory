"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import type { ApiError } from "@/types/api-common"
import { SODetailView } from "../components/sales-orders/so-detail-view"
import {
  useSalesOrder,
  useConfirmSalesOrder,
  useCancelSalesOrder,
} from "../hooks/use-sales-orders"

interface SODetailPageProps {
  params: Promise<{ id: string }>
}

export function SODetailPage({ params }: SODetailPageProps) {
  const { id } = use(params)
  const orderId = Number(id)
  const router = useRouter()
  const t = useTranslations("Sales.salesOrders.detail")
  const { data: order, isLoading, error } = useSalesOrder(orderId)
  const confirmMutation = useConfirmSalesOrder()
  const cancelMutation = useCancelSalesOrder()

  const handleConfirm = React.useCallback(() => {
    if (!order) return
    if (!confirm(t("confirmPrompt", { orderNumber: order.order_number })))
      return
    confirmMutation.mutate(order.id, {
      onSuccess: () =>
        toast.success(t("toastConfirmed", { orderNumber: order.order_number })),
      onError: (err: unknown) => {
        const e = err as unknown as ApiError
        toast.error(e.message || t("confirmFailed"))
      },
    })
  }, [order, confirmMutation, t])

  const handleCancel = React.useCallback(() => {
    if (!order) return
    if (!confirm(t("cancelPrompt", { orderNumber: order.order_number }))) return
    cancelMutation.mutate(order.id, {
      onSuccess: () =>
        toast.success(t("toastCancelled", { orderNumber: order.order_number })),
      onError: (err: unknown) => {
        const e = err as unknown as ApiError
        toast.error(e.message || t("cancelFailed"))
      },
    })
  }, [order, cancelMutation, t])

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />
      <SODetailView
        order={order}
        isLoading={isLoading}
        error={error}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        onBack={() => router.push("/sales/sales-orders")}
        isConfirming={confirmMutation.isPending}
        isCancelling={cancelMutation.isPending}
      />
    </div>
  )
}
