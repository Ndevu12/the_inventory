"use client"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { SOStatusBadge } from "./so-status-badge"
import { CanFulfillBadge } from "./can-fulfill-badge"
import type { SalesOrder } from "../../types/sales.types"

interface SODetailViewProps {
  order: SalesOrder | undefined
  isLoading: boolean
  error: unknown
  onConfirm: () => void
  onCancel: () => void
  onBack: () => void
  isConfirming: boolean
  isCancelling: boolean
}

export function SODetailView({
  order,
  isLoading,
  error,
  onConfirm,
  onCancel,
  onBack,
  isConfirming,
  isCancelling,
}: SODetailViewProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !order) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          Sales order not found.
        </CardContent>
      </Card>
    )
  }

  const orderDate = new Date(order.order_date).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-xl">{order.order_number}</CardTitle>
              <CardDescription>
                {order.customer_name} &middot; {orderDate}
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <SOStatusBadge status={order.status} />
              <CanFulfillBadge canFulfill={order.can_fulfill} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <InfoItem label="Order Number" value={order.order_number} />
            <InfoItem label="Customer" value={order.customer_name} />
            <InfoItem label="Order Date" value={orderDate} />
            <InfoItem label="Status" value={order.status_display} />
            <InfoItem
              label="Total Price"
              value={parseFloat(order.total_price).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            />
            <InfoItem
              label="Created"
              value={new Date(order.created_at).toLocaleDateString()}
            />
          </div>
          {order.notes && (
            <>
              <Separator className="my-4" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Notes</p>
                <p className="mt-1 text-sm whitespace-pre-wrap">{order.notes}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Line Items</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Unit Price</TableHead>
                <TableHead className="text-right">Line Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {order.lines.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No line items.
                  </TableCell>
                </TableRow>
              ) : (
                order.lines.map((line) => (
                  <TableRow key={line.id}>
                    <TableCell className="font-medium">{line.product_name}</TableCell>
                    <TableCell className="text-muted-foreground">{line.product_sku}</TableCell>
                    <TableCell className="text-right tabular-nums">{line.quantity}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {parseFloat(line.unit_price).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell className="text-right font-medium tabular-nums">
                      {parseFloat(line.line_total).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
            {order.lines.length > 0 && (
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={4} className="text-right font-semibold">
                    Order Total
                  </TableCell>
                  <TableCell className="text-right font-bold tabular-nums">
                    {parseFloat(order.total_price).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                </TableRow>
              </TableFooter>
            )}
          </Table>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        {order.status === "draft" && (
          <Button onClick={onConfirm} disabled={isConfirming}>
            {isConfirming ? "Confirming..." : "Confirm Order"}
          </Button>
        )}
        {(order.status === "draft" || order.status === "confirmed") && (
          <Button
            variant="destructive"
            onClick={onCancel}
            disabled={isCancelling}
          >
            {isCancelling ? "Cancelling..." : "Cancel Order"}
          </Button>
        )}
        <Button variant="outline" onClick={onBack}>
          Back to Orders
        </Button>
      </div>
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-sm">{value}</p>
    </div>
  )
}
