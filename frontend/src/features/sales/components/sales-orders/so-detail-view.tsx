"use client"

import { useLocale, useTranslations } from "next-intl"
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
  const locale = useLocale()
  const t = useTranslations("Sales.salesOrders.detailView")
  const tSoStatus = useTranslations("Sales.soStatus")

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
          {t("notFound")}
        </CardContent>
      </Card>
    )
  }

  const orderDate = new Date(order.order_date).toLocaleDateString(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  const createdDate = new Date(order.created_at).toLocaleDateString(locale)

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
            <InfoItem label={t("orderNumber")} value={order.order_number} />
            <InfoItem label={t("customer")} value={order.customer_name} />
            <InfoItem label={t("orderDate")} value={orderDate} />
            <InfoItem label={t("status")} value={tSoStatus(order.status)} />
            <InfoItem
              label={t("totalPrice")}
              value={parseFloat(order.total_price).toLocaleString(locale, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            />
            <InfoItem label={t("created")} value={createdDate} />
          </div>
          {order.notes && (
            <>
              <Separator className="my-4" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {t("notesLabel")}
                </p>
                <p className="mt-1 text-sm whitespace-pre-wrap">{order.notes}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("lineItemsTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("colProduct")}</TableHead>
                <TableHead>{t("colSku")}</TableHead>
                <TableHead className="text-right">{t("colQty")}</TableHead>
                <TableHead className="text-right">{t("colUnitPrice")}</TableHead>
                <TableHead className="text-right">{t("colLineTotal")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {order.lines.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-center text-muted-foreground"
                  >
                    {t("noLineItems")}
                  </TableCell>
                </TableRow>
              ) : (
                order.lines.map((line) => (
                  <TableRow key={line.id}>
                    <TableCell className="font-medium">
                      {line.product_name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {line.product_sku}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {line.quantity}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {parseFloat(line.unit_price).toLocaleString(locale, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell className="text-right font-medium tabular-nums">
                      {parseFloat(line.line_total).toLocaleString(locale, {
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
                    {t("orderTotal")}
                  </TableCell>
                  <TableCell className="text-right font-bold tabular-nums">
                    {parseFloat(order.total_price).toLocaleString(locale, {
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
            {isConfirming ? t("confirming") : t("confirmOrder")}
          </Button>
        )}
        {(order.status === "draft" || order.status === "confirmed") && (
          <Button
            variant="destructive"
            onClick={onCancel}
            disabled={isCancelling}
          >
            {isCancelling ? t("cancelling") : t("cancelOrder")}
          </Button>
        )}
        <Button variant="outline" onClick={onBack}>
          {t("backToOrders")}
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
