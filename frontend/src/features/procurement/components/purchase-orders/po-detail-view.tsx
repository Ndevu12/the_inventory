"use client"

import { useLocale, useTranslations } from "next-intl"
import { CheckCircleIcon, XCircleIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from "@/components/ui/table"

import type { PurchaseOrder } from "../../types/procurement.types"
import { POStatusBadge } from "./po-status-badge"

interface PODetailViewProps {
  order: PurchaseOrder
  onConfirm?: () => void
  onCancel?: () => void
  isConfirming?: boolean
  isCancelling?: boolean
}

export function PODetailView({
  order,
  onConfirm,
  onCancel,
  isConfirming = false,
  isCancelling = false,
}: PODetailViewProps) {
  const locale = useLocale()
  const t = useTranslations("Procurement.purchaseOrders.detailView")
  const tShared = useTranslations("Procurement.shared")

  const canConfirm = order.status === "draft"
  const canCancel = order.status === "draft" || order.status === "confirmed"

  const formatCurrency = (value: string | number) =>
    new Intl.NumberFormat(locale, {
      style: "currency",
      currency: "USD",
    }).format(Number(value))

  const formatDate = (value: string | null) =>
    value ? new Date(value).toLocaleDateString(locale) : tShared("emDash")

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-xl">
                {order.order_number}
              </CardTitle>
              <CardDescription>{order.supplier_name}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <POStatusBadge status={order.status} />
              {canConfirm && onConfirm && (
                <Button
                  size="sm"
                  onClick={onConfirm}
                  disabled={isConfirming}
                >
                  <CheckCircleIcon className="mr-1 size-4" />
                  {isConfirming ? t("confirming") : t("confirm")}
                </Button>
              )}
              {canCancel && onCancel && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={onCancel}
                  disabled={isCancelling}
                >
                  <XCircleIcon className="mr-1 size-4" />
                  {isCancelling ? t("cancelling") : t("cancelOrder")}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("orderDate")}
              </dt>
              <dd className="mt-1 text-sm">{formatDate(order.order_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("expectedDelivery")}
              </dt>
              <dd className="mt-1 text-sm">
                {formatDate(order.expected_delivery_date)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("totalCost")}
              </dt>
              <dd className="mt-1 text-sm font-semibold">
                {formatCurrency(order.total_cost)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("created")}
              </dt>
              <dd className="mt-1 text-sm">
                {formatDate(order.created_at)}
              </dd>
            </div>
          </dl>
          {order.notes && (
            <div className="mt-4">
              <dt className="text-sm font-medium text-muted-foreground">
                {t("notes")}
              </dt>
              <dd className="mt-1 whitespace-pre-wrap text-sm">
                {order.notes}
              </dd>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("lineItemsTitle")}</CardTitle>
          <CardDescription>
            {t("lineItemsCount", { count: order.lines.length })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("colProduct")}</TableHead>
                  <TableHead>{t("colSku")}</TableHead>
                  <TableHead className="text-right">{t("colQuantity")}</TableHead>
                  <TableHead className="text-right">{t("colUnitCost")}</TableHead>
                  <TableHead className="text-right">{t("colLineTotal")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {order.lines.map((line) => (
                  <TableRow key={line.id}>
                    <TableCell className="font-medium">
                      {line.product_name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {line.product_sku}
                    </TableCell>
                    <TableCell className="text-right">
                      {line.quantity}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(line.unit_cost)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(line.line_total)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={4} className="text-right font-semibold">
                    {t("grandTotal")}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {formatCurrency(order.total_cost)}
                  </TableCell>
                </TableRow>
              </TableFooter>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
