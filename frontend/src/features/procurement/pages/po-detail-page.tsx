"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "@/i18n/navigation"
import { ArrowLeftIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
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
  const t = useTranslations("Procurement.purchaseOrders.detail")
  const tAct = useTranslations("Procurement.purchaseOrders.actions")
  const tShared = useTranslations("Procurement.shared")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")
  const { data: order, isLoading } = usePurchaseOrder(id)

  const confirmMutation = useConfirmPurchaseOrder()
  const cancelMutation = useCancelPurchaseOrder()

  const [cancelDialogOpen, setCancelDialogOpen] = React.useState(false)

  function handleConfirm() {
    confirmMutation.mutate(id, {
      onSuccess: () => toast.success(t("toastConfirmed")),
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? tShared("unknownError")
        toast.error(t("confirmFailed", { message }))
      },
    })
  }

  function handleCancel() {
    setCancelDialogOpen(true)
  }

  function confirmCancelPo() {
    cancelMutation.mutate(id, {
      onSuccess: () => {
        toast.success(t("toastCancelled"))
        setCancelDialogOpen(false)
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? tShared("unknownError")
        toast.error(t("cancelFailed", { message }))
      },
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={
          order
            ? t("title", { orderNumber: order.order_number })
            : t("titleLoading")
        }
        description={order?.supplier_name}
        actions={
          <Button
            variant="outline"
            onClick={() => router.push("/procurement/purchase-orders")}
          >
            <ArrowLeftIcon className="mr-2 size-4" />
            {t("backToList")}
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

      <AlertDialog
        open={cancelDialogOpen}
        onOpenChange={(open) => {
          setCancelDialogOpen(open)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tAct("cancel")}</AlertDialogTitle>
            <AlertDialogDescription>{t("cancelConfirm")}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelMutation.isPending}>
              {tCommon("cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={confirmCancelPo}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending
                ? tCommonStates("loading")
                : tAct("cancel")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
