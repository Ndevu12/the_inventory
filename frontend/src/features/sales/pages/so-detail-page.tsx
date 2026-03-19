"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
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
  const { data: order, isLoading, error } = useSalesOrder(orderId)
  const confirmMutation = useConfirmSalesOrder()
  const cancelMutation = useCancelSalesOrder()

  const handleConfirm = React.useCallback(() => {
    if (!order) return
    if (!confirm(`Confirm sales order "${order.order_number}"?`)) return
    confirmMutation.mutate(order.id, {
      onSuccess: () => toast.success(`Order "${order.order_number}" confirmed`),
      onError: (err) => {
        const message = (err as { message?: string }).message ?? "Failed to confirm order"
        toast.error(message)
      },
    })
  }, [order, confirmMutation])

  const handleCancel = React.useCallback(() => {
    if (!order) return
    if (!confirm(`Cancel sales order "${order.order_number}"? This cannot be undone.`)) return
    cancelMutation.mutate(order.id, {
      onSuccess: () => toast.success(`Order "${order.order_number}" cancelled`),
      onError: (err) => {
        const message = (err as { message?: string }).message ?? "Failed to cancel order"
        toast.error(message)
      },
    })
  }, [order, cancelMutation])

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Sales Order Details"
        description="View order information, line items, and manage order status"
      />
      <SODetailView
        order={order}
        isLoading={isLoading}
        error={error}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        onBack={() => router.push("/sales/orders")}
        isConfirming={confirmMutation.isPending}
        isCancelling={cancelMutation.isPending}
      />
    </div>
  )
}
