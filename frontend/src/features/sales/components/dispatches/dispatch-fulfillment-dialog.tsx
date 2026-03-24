"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ApiError } from "@/types/api-common"

import {
  useDispatchFulfillmentPreview,
  useProcessDispatch,
} from "../../hooks/use-dispatches"
import type { Dispatch } from "../../types/dispatch.types"

function errorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "message" in err) {
    const m = (err as ApiError).message
    if (typeof m === "string" && m) return m
  }
  return fallback
}

interface DispatchFulfillmentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dispatch: Dispatch | null
  /** Shown above the generic guidance (e.g. API error from full process). */
  introText?: string
}

export function DispatchFulfillmentDialog({
  open,
  onOpenChange,
  dispatch,
  introText,
}: DispatchFulfillmentDialogProps) {
  const t = useTranslations("Sales.dispatches.fulfillmentDialog")
  const tList = useTranslations("Sales.dispatches.list")

  const dispatchId = dispatch?.id ?? null
  const previewQuery = useDispatchFulfillmentPreview(dispatchId, open)
  const processMutation = useProcessDispatch()

  const handleIssueAvailable = React.useCallback(() => {
    if (!dispatch) return
    processMutation.mutate(
      { id: dispatch.id, issueAvailableOnly: true },
      {
        onSuccess: () => {
          toast.success(
            tList("toastProcessedPartial", {
              dispatchNumber: dispatch.dispatch_number,
            }),
          )
          onOpenChange(false)
        },
        onError: (error: unknown) => {
          toast.error(errorMessage(error, t("genericError")))
        },
      },
    )
  }, [dispatch, onOpenChange, processMutation, t, tList])

  const soHref = dispatch
    ? `/sales/sales-orders/${dispatch.sales_order}`
    : "/sales/sales-orders"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" showCloseButton>
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription className="space-y-2">
            {introText ? (
              <span className="text-foreground block">{introText}</span>
            ) : null}
            <span className="block">{t("description")}</span>
          </DialogDescription>
        </DialogHeader>

        {previewQuery.isLoading ? (
          <p className="text-muted-foreground text-sm">{t("loading")}</p>
        ) : previewQuery.isError ? (
          <p className="text-destructive text-sm">
            {errorMessage(previewQuery.error, t("genericError"))}
          </p>
        ) : previewQuery.data ? (
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs">
              {t("fromLabel")}{" "}
              <span className="text-foreground font-medium">
                {previewQuery.data.from_location.name}
              </span>
            </p>
            <div className="max-h-64 overflow-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("colProduct")}</TableHead>
                    <TableHead className="text-right">{t("colOrdered")}</TableHead>
                    <TableHead className="text-right">
                      {t("colAvailable")}
                    </TableHead>
                    <TableHead className="text-right">{t("colShipNow")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {previewQuery.data.lines.map((row) => (
                    <TableRow key={row.line_id}>
                      <TableCell>
                        <span className="font-medium">{row.product_sku}</span>
                        {row.product_name ? (
                          <span className="text-muted-foreground block text-xs">
                            {row.product_name}
                          </span>
                        ) : null}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {row.ordered_quantity}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {row.available_quantity}
                      </TableCell>
                      <TableCell className="text-right tabular-nums font-medium">
                        {row.issue_now_quantity}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : null}

        <DialogFooter showCloseButton>
          {dispatch ? (
            <Button variant="outline" render={<Link href={soHref} />}>
              {t("openSalesOrder")}
            </Button>
          ) : null}
          <Button
            disabled={
              !previewQuery.data ||
              previewQuery.data.total_issue_if_available_only <= 0 ||
              processMutation.isPending
            }
            onClick={handleIssueAvailable}
          >
            {t("issueAvailable")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
