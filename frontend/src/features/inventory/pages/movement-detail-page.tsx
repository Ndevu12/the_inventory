"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { Link } from "@/i18n/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { useMovement } from "../hooks/use-movements"
import type { MovementType } from "../api/movements-api"

const TYPE_VARIANT: Record<
  MovementType,
  "default" | "secondary" | "outline" | "destructive"
> = {
  receive: "default",
  issue: "destructive",
  transfer: "secondary",
  adjustment: "outline",
}

interface MovementDetailPageProps {
  params: Promise<{ id: string }>
}

function formatDateTime(iso: string) {
  const d = new Date(iso)
  return `${d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })} ${d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  })}`
}

export function MovementDetailPage({ params }: MovementDetailPageProps) {
  const t = useTranslations("Inventory")
  const { id } = use(params)
  const movementId = Number(id)
  const invalidId = !Number.isFinite(movementId) || movementId <= 0

  const { data: movement, isLoading, isError } = useMovement(
    invalidId ? 0 : movementId,
  )

  if (invalidId) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("movements.detail.invalidTitle")} />
        <p className="text-muted-foreground">
          {t("movements.detail.invalidBody")}
        </p>
        <Button variant="outline" asChild>
          <Link href="/stock/movements">
            <ArrowLeftIcon className="mr-2 size-4" />
            {t("movements.detail.backToList")}
          </Link>
        </Button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (isError || !movement) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("movements.detail.notFoundTitle")} />
        <p className="text-muted-foreground">
          {t("movements.detail.notFoundBody")}
        </p>
        <Button variant="outline" asChild>
          <Link href="/stock/movements">
            <ArrowLeftIcon className="mr-2 size-4" />
            {t("movements.detail.backToList")}
          </Link>
        </Button>
      </div>
    )
  }

  const type = movement.movement_type

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("movements.detail.title", { id: movement.id })}
        description={movement.movement_type_display}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" asChild size="sm">
              <Link href="/stock/movements">
                <ArrowLeftIcon className="mr-2 size-4" />
                {t("movements.detail.allMovements")}
              </Link>
            </Button>
            <Button variant="outline" asChild size="sm">
              <Link href={`/products/${movement.product}`}>
                {t("movements.detail.viewProduct")}
              </Link>
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">
            {t("movements.detail.summary")}
          </CardTitle>
          <Badge variant={TYPE_VARIANT[type]}>
            {movement.movement_type_display}
          </Badge>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.productSku")}
              </dt>
              <dd className="mt-1 font-medium">{movement.product_sku}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.quantity")}
              </dt>
              <dd className="mt-1 font-mono tabular-nums">{movement.quantity}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.fromLocation")}
              </dt>
              <dd className="mt-1">
                {movement.from_location_name ?? t("shared.emDash")}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.toLocation")}
              </dt>
              <dd className="mt-1">
                {movement.to_location_name ?? t("shared.emDash")}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.unitCost")}
              </dt>
              <dd className="mt-1">
                {movement.unit_cost != null ? movement.unit_cost : t("shared.emDash")}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.reference")}
              </dt>
              <dd className="mt-1">
                {movement.reference || t("shared.emDash")}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.notes")}
              </dt>
              <dd className="mt-1 whitespace-pre-wrap">
                {movement.notes || t("shared.emDash")}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                {t("movements.detail.created")}
              </dt>
              <dd className="mt-1 text-sm text-muted-foreground">
                {formatDateTime(movement.created_at)}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {movement.lot_allocations.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t("movements.detail.lotAllocations")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("movements.detail.lotNumber")}</TableHead>
                  <TableHead className="text-right">
                    {t("movements.detail.lotQty")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {movement.lot_allocations.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-mono text-sm">
                      {row.lot_number}
                    </TableCell>
                    <TableCell className="text-right font-mono tabular-nums">
                      {row.quantity}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
