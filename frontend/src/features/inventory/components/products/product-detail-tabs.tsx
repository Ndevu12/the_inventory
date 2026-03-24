"use client"

import { useTranslations } from "next-intl"
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs"
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
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

import type {
  Product,
  StockRecord,
  StockMovement,
  StockLot,
} from "../../types/inventory.types"
import {
  formatCurrency,
  formatDate,
  formatDateTime,
} from "../../helpers/inventory-formatters"

interface ProductDetailTabsProps {
  product: Product
  stockRecords?: StockRecord[]
  movements?: StockMovement[]
  lots?: StockLot[]
  isLoadingStock?: boolean
  isLoadingMovements?: boolean
  isLoadingLots?: boolean
}

export function ProductDetailTabs({
  product,
  stockRecords,
  movements,
  lots,
  isLoadingStock,
  isLoadingMovements,
  isLoadingLots,
}: ProductDetailTabsProps) {
  const t = useTranslations("Inventory")

  return (
    <Tabs defaultValue="info">
      <TabsList>
        <TabsTrigger value="info">{t("products.tabs.info")}</TabsTrigger>
        <TabsTrigger value="stock">{t("products.tabs.stock")}</TabsTrigger>
        <TabsTrigger value="movements">
          {t("products.tabs.movements")}
        </TabsTrigger>
        <TabsTrigger value="lots">{t("products.tabs.lots")}</TabsTrigger>
      </TabsList>

      <TabsContent value="info" className="mt-4">
        <InfoTab product={product} />
      </TabsContent>

      <TabsContent value="stock" className="mt-4">
        <StockTab records={stockRecords} isLoading={isLoadingStock} />
      </TabsContent>

      <TabsContent value="movements" className="mt-4">
        <MovementsTab movements={movements} isLoading={isLoadingMovements} />
      </TabsContent>

      <TabsContent value="lots" className="mt-4">
        <LotsTab lots={lots} isLoading={isLoadingLots} />
      </TabsContent>
    </Tabs>
  )
}

function InfoTab({ product }: { product: Product }) {
  const t = useTranslations("Inventory")
  const fields = [
    { label: t("products.detail.fields.sku"), value: product.sku },
    { label: t("products.detail.fields.name"), value: product.name },
    {
      label: t("products.detail.fields.category"),
      value: product.category_name ?? t("shared.emDash"),
    },
    {
      label: t("products.detail.fields.unitOfMeasure"),
      value: product.unit_of_measure_display,
    },
    {
      label: t("products.detail.fields.unitCost"),
      value: formatCurrency(product.unit_cost),
    },
    {
      label: t("products.detail.fields.reorderPoint"),
      value: product.reorder_point,
    },
    {
      label: t("products.detail.fields.status"),
      value: product.is_active ? t("shared.active") : t("shared.inactive"),
    },
    {
      label: t("products.detail.fields.created"),
      value: formatDateTime(product.created_at),
    },
    {
      label: t("products.detail.fields.updated"),
      value: formatDateTime(product.updated_at),
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("products.detail.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {fields.map((f) => (
            <div key={f.label}>
              <dt className="text-sm text-muted-foreground">{f.label}</dt>
              <dd className="text-sm font-medium">{f.value}</dd>
            </div>
          ))}
        </dl>
        {product.description && (
          <div className="mt-4">
            <dt className="text-sm text-muted-foreground">
              {t("products.detail.description")}
            </dt>
            <dd
              className="prose prose-sm dark:prose-invert mt-1 max-w-none"
              dangerouslySetInnerHTML={{ __html: product.description }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StockTab({
  records,
  isLoading,
}: {
  records?: StockRecord[]
  isLoading?: boolean
}) {
  const t = useTranslations("Inventory")
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("products.stockTab.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {!records?.length ? (
          <p className="text-sm text-muted-foreground">
            {t("products.stockTab.empty")}
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("products.stockTab.location")}</TableHead>
                <TableHead className="text-right">
                  {t("products.stockTab.quantity")}
                </TableHead>
                <TableHead className="text-right">
                  {t("products.stockTab.reserved")}
                </TableHead>
                <TableHead className="text-right">
                  {t("products.stockTab.available")}
                </TableHead>
                <TableHead>{t("products.stockTab.status")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.location_name}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {r.quantity}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {r.reserved_quantity}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {r.available_quantity}
                  </TableCell>
                  <TableCell>
                    {r.is_low_stock ? (
                      <Badge variant="destructive">
                        {t("shared.lowStock")}
                      </Badge>
                    ) : (
                      <Badge variant="secondary">{t("shared.ok")}</Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function MovementsTab({
  movements,
  isLoading,
}: {
  movements?: StockMovement[]
  isLoading?: boolean
}) {
  const t = useTranslations("Inventory")
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("products.movementsTab.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {!movements?.length ? (
          <p className="text-sm text-muted-foreground">
            {t("products.movementsTab.empty")}
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("products.movementsTab.type")}</TableHead>
                <TableHead className="text-right">
                  {t("products.movementsTab.qty")}
                </TableHead>
                <TableHead>{t("products.movementsTab.from")}</TableHead>
                <TableHead>{t("products.movementsTab.to")}</TableHead>
                <TableHead>{t("products.movementsTab.reference")}</TableHead>
                <TableHead>{t("products.movementsTab.date")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {movements.map((m) => (
                <TableRow key={m.id}>
                  <TableCell>
                    <Badge variant="outline">
                      {m.movement_type_display}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {m.quantity}
                  </TableCell>
                  <TableCell>
                    {m.from_location_name ?? t("shared.emDash")}
                  </TableCell>
                  <TableCell>
                    {m.to_location_name ?? t("shared.emDash")}
                  </TableCell>
                  <TableCell className="max-w-[150px] truncate">
                    {m.reference || t("shared.emDash")}
                  </TableCell>
                  <TableCell>{formatDate(m.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function LotsTab({
  lots,
  isLoading,
}: {
  lots?: StockLot[]
  isLoading?: boolean
}) {
  const t = useTranslations("Inventory")
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("products.lotsTab.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {!lots?.length ? (
          <p className="text-sm text-muted-foreground">
            {t("products.lotsTab.empty")}
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("products.lotsTab.lotNumber")}</TableHead>
                <TableHead className="text-right">
                  {t("products.lotsTab.received")}
                </TableHead>
                <TableHead className="text-right">
                  {t("products.lotsTab.remaining")}
                </TableHead>
                <TableHead>{t("products.lotsTab.expiry")}</TableHead>
                <TableHead>{t("products.lotsTab.status")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lots.map((lot) => (
                <TableRow key={lot.id}>
                  <TableCell className="font-mono text-xs">
                    {lot.lot_number}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {lot.quantity_received}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {lot.quantity_remaining}
                  </TableCell>
                  <TableCell>
                    {lot.expiry_date ? (
                      <ExpiryDisplay
                        date={lot.expiry_date}
                        daysToExpiry={lot.days_to_expiry}
                        isExpired={lot.is_expired}
                      />
                    ) : (
                      t("shared.emDash")
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={lot.is_active ? "default" : "secondary"}
                    >
                      {lot.is_active ? t("shared.active") : t("shared.inactive")}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function ExpiryDisplay({
  date,
  daysToExpiry,
  isExpired,
}: {
  date: string
  daysToExpiry: number | null
  isExpired: boolean
}) {
  const t = useTranslations("Inventory")
  let variant: "destructive" | "secondary" | "outline" = "outline"
  if (isExpired) variant = "destructive"
  else if (daysToExpiry !== null && daysToExpiry <= 30) variant = "secondary"

  return (
    <Badge variant={variant}>
      {formatDate(date)}
      {daysToExpiry !== null && !isExpired && ` ${t("shared.daysSuffix", { days: daysToExpiry })}`}
      {isExpired && ` ${t("shared.expiredSuffix")}`}
    </Badge>
  )
}

function TableSkeleton() {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
