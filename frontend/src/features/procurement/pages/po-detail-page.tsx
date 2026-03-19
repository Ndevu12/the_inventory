"use client"

import { use } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeftIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"

import {
  usePurchaseOrder,
  useConfirmPurchaseOrder,
  useCancelPurchaseOrder,
} from "../hooks/use-purchase-orders"
import { PODetailView } from "../components/purchase-orders/po-detail-view"

interface PODetailPageProps {
  params: Promise<{ id: string }>
}

export function PODetailPage({ params }: PODetailPageProps) {
  const { id: rawId } = use(params)
  const id = Number(rawId)
  const router = useRouter()
  const { data: order, isLoading } = usePurchaseOrder(id)

  const confirmMutation = useConfirmPurchaseOrder()
  const cancelMutation = useCancelPurchaseOrder()

  function handleConfirm() {
    confirmMutation.mutate(id, {
      onSuccess: () => toast.success("Purchase order confirmed"),
      onError: (error) =>
        toast.error(
          `Failed to confirm: ${(error as { message?: string }).message ?? "Unknown error"}`,
        ),
    })
  }

  function handleCancel() {
    if (!confirm("Cancel this purchase order?")) return
    cancelMutation.mutate(id, {
      onSuccess: () => toast.success("Purchase order cancelled"),
      onError: (error) =>
        toast.error(
          `Failed to cancel: ${(error as { message?: string }).message ?? "Unknown error"}`,
        ),
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={order ? `PO: ${order.order_number}` : "Purchase Order"}
        description={order?.supplier_name}
        actions={
          <Button
            variant="outline"
            onClick={() => router.push("/procurement/purchase-orders")}
          >
            <ArrowLeftIcon className="mr-2 size-4" />
            Back to List
          </Button>
        }
      />

      {isLoading || !order ? (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <PODetailView
          order={order}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          isConfirming={confirmMutation.isPending}
          isCancelling={cancelMutation.isPending}
        />
      )}
    </div>
  )
}
