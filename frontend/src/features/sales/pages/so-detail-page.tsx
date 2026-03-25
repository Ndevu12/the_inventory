"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "@/i18n/navigation"
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
  const tAct = useTranslations("Sales.salesOrders.actions")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")
  const { data: order, isLoading, error } = useSalesOrder(orderId)
  const confirmMutation = useConfirmSalesOrder()
  const cancelMutation = useCancelSalesOrder()

  const [actionDialog, setActionDialog] = React.useState<
    "confirm" | "cancel" | null
  >(null)

  const handleConfirm = React.useCallback(() => {
    setActionDialog("confirm")
  }, [])

  const handleCancel = React.useCallback(() => {
    setActionDialog("cancel")
  }, [])

  const runDialogAction = React.useCallback(() => {
    if (!order) return
    if (actionDialog === "confirm") {
      confirmMutation.mutate(order.id, {
        onSuccess: () => {
          toast.success(
            t("toastConfirmed", { orderNumber: order.order_number }),
          )
          setActionDialog(null)
        },
        onError: (err: unknown) => {
          const e = err as unknown as ApiError
          toast.error(e.message || t("confirmFailed"))
        },
      })
      return
    }
    if (actionDialog === "cancel") {
      cancelMutation.mutate(order.id, {
        onSuccess: () => {
          toast.success(
            t("toastCancelled", { orderNumber: order.order_number }),
          )
          setActionDialog(null)
        },
        onError: (err: unknown) => {
          const e = err as unknown as ApiError
          toast.error(e.message || t("cancelFailed"))
        },
      })
    }
  }, [
    order,
    actionDialog,
    confirmMutation,
    cancelMutation,
    t,
  ])

  const dialogPending =
    (actionDialog === "confirm" && confirmMutation.isPending) ||
    (actionDialog === "cancel" && cancelMutation.isPending)

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

      <AlertDialog
        open={actionDialog != null && order != null}
        onOpenChange={(open) => {
          if (!open) setActionDialog(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionDialog === "confirm" ? tAct("confirm") : tAct("cancel")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {order && actionDialog === "confirm"
                ? t("confirmPrompt", { orderNumber: order.order_number })
                : order && actionDialog === "cancel"
                  ? t("cancelPrompt", { orderNumber: order.order_number })
                  : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={dialogPending}>
              {tCommon("cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              variant={actionDialog === "confirm" ? "default" : "destructive"}
              onClick={runDialogAction}
              disabled={dialogPending}
            >
              {dialogPending
                ? tCommonStates("loading")
                : actionDialog === "confirm"
                  ? tAct("confirm")
                  : tAct("cancel")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
