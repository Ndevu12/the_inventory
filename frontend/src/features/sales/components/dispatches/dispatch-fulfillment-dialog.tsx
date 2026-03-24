"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
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

function errorMessage(err: unknown): string {
  if (err && typeof err === "object" && "message" in err) {
    const m = (err as ApiError).message
    if (typeof m === "string" && m) return m
  }
  return "Something went wrong."
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
            `Dispatch "${dispatch.dispatch_number}" processed — issued available quantities.`,
          )
          onOpenChange(false)
        },
        onError: (error: unknown) => {
          toast.error(errorMessage(error))
        },
      },
    )
  }, [dispatch, onOpenChange, processMutation])

  const soHref = dispatch
    ? `/sales/sales-orders/${dispatch.sales_order}`
    : "/sales/sales-orders"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" showCloseButton>
        <DialogHeader>
          <DialogTitle>Stock at dispatch source</DialogTitle>
          <DialogDescription className="space-y-2">
            {introText ? (
              <span className="text-foreground block">{introText}</span>
            ) : null}
            <span className="block">
              Per line: ordered quantity vs unreserved stock at the dispatch
              source. You can issue only what is available now, open the sales
              order to reduce line quantities or cancel the dispatch, or
              receive/transfer stock into this location first.
            </span>
          </DialogDescription>
        </DialogHeader>

        {previewQuery.isLoading ? (
          <p className="text-muted-foreground text-sm">Loading preview…</p>
        ) : previewQuery.isError ? (
          <p className="text-destructive text-sm">
            {errorMessage(previewQuery.error)}
          </p>
        ) : previewQuery.data ? (
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs">
              From:{" "}
              <span className="text-foreground font-medium">
                {previewQuery.data.from_location.name}
              </span>
            </p>
            <div className="max-h-64 overflow-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead className="text-right">Ordered</TableHead>
                    <TableHead className="text-right">Available</TableHead>
                    <TableHead className="text-right">Ship now</TableHead>
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
              Open sales order
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
            Issue available quantities
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
