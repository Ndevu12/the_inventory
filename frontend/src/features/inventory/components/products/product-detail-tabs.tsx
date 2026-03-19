"use client"

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
  return (
    <Tabs defaultValue="info">
      <TabsList>
        <TabsTrigger value="info">Info</TabsTrigger>
        <TabsTrigger value="stock">Stock Records</TabsTrigger>
        <TabsTrigger value="movements">Movements</TabsTrigger>
        <TabsTrigger value="lots">Lots</TabsTrigger>
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
  const fields = [
    { label: "SKU", value: product.sku },
    { label: "Name", value: product.name },
    { label: "Category", value: product.category_name ?? "—" },
    { label: "Unit of Measure", value: product.unit_of_measure_display },
    { label: "Unit Cost", value: formatCurrency(product.unit_cost) },
    { label: "Reorder Point", value: product.reorder_point },
    { label: "Status", value: product.is_active ? "Active" : "Inactive" },
    { label: "Created", value: formatDateTime(product.created_at) },
    { label: "Updated", value: formatDateTime(product.updated_at) },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Product Details</CardTitle>
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
            <dt className="text-sm text-muted-foreground">Description</dt>
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
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stock by Location</CardTitle>
      </CardHeader>
      <CardContent>
        {!records?.length ? (
          <p className="text-sm text-muted-foreground">No stock records.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Location</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Reserved</TableHead>
                <TableHead className="text-right">Available</TableHead>
                <TableHead>Status</TableHead>
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
                      <Badge variant="destructive">Low Stock</Badge>
                    ) : (
                      <Badge variant="secondary">OK</Badge>
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
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Movements</CardTitle>
      </CardHeader>
      <CardContent>
        {!movements?.length ? (
          <p className="text-sm text-muted-foreground">No movements yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Date</TableHead>
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
                  <TableCell>{m.from_location_name ?? "—"}</TableCell>
                  <TableCell>{m.to_location_name ?? "—"}</TableCell>
                  <TableCell className="max-w-[150px] truncate">
                    {m.reference || "—"}
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
  if (isLoading) return <TableSkeleton />

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lots / Batches</CardTitle>
      </CardHeader>
      <CardContent>
        {!lots?.length ? (
          <p className="text-sm text-muted-foreground">No lots tracked.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lot #</TableHead>
                <TableHead className="text-right">Received</TableHead>
                <TableHead className="text-right">Remaining</TableHead>
                <TableHead>Expiry</TableHead>
                <TableHead>Status</TableHead>
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
                      "—"
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={lot.is_active ? "default" : "secondary"}
                    >
                      {lot.is_active ? "Active" : "Inactive"}
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
  let variant: "destructive" | "secondary" | "outline" = "outline"
  if (isExpired) variant = "destructive"
  else if (daysToExpiry !== null && daysToExpiry <= 30) variant = "secondary"

  return (
    <Badge variant={variant}>
      {formatDate(date)}
      {daysToExpiry !== null && !isExpired && ` (${daysToExpiry}d)`}
      {isExpired && " (expired)"}
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
