"use client"

import { useRouter } from "@/i18n/navigation"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"
import { useAllProducts } from "@/features/inventory/hooks/use-products"

import { useCreatePurchaseOrder } from "../hooks/use-purchase-orders"
import { useActiveSuppliers } from "../hooks/use-suppliers"
import { POForm } from "../components/purchase-orders/po-form"
import type { PurchaseOrderCreatePayload } from "../types/procurement.types"
import type { CreatePurchaseOrderFormValues } from "../helpers/po-schemas"

export function POCreatePage() {
  const router = useRouter()
  const createMutation = useCreatePurchaseOrder()
  const { data: suppliers, isLoading: suppliersLoading } = useActiveSuppliers()
  const { data: products, isLoading: productsLoading } = useAllProducts()

  const isLoading = suppliersLoading || productsLoading

  function handleSubmit(values: CreatePurchaseOrderFormValues) {
    const payload: PurchaseOrderCreatePayload = {
      supplier: values.supplier,
      order_date: values.order_date,
      expected_delivery_date: values.expected_delivery_date || null,
      notes: values.notes,
      lines: values.lines.map((l) => ({
        product: l.product,
        quantity: l.quantity,
        unit_cost: l.unit_cost,
      })),
    }

    createMutation.mutate(payload, {
      onSuccess: () => {
        toast.success("Purchase order created successfully")
        router.push("/procurement/purchase-orders")
      },
      onError: (error) => {
        toast.error(
          `Failed to create purchase order: ${(error as { message?: string }).message ?? "Unknown error"}`,
        )
      },
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Purchase Order"
        description="Place a new order with a supplier."
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <POForm
          suppliers={(suppliers ?? []).map((s) => ({
            id: s.id,
            name: s.name,
            code: s.code,
          }))}
          products={products ?? []}
          onSubmit={handleSubmit}
          onCancel={() => router.push("/procurement/purchase-orders")}
          isSubmitting={createMutation.isPending}
        />
      )}
    </div>
  )
}
