"use client"

import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { SOForm } from "../components/sales-orders/so-form"
import { useCreateSalesOrder, useSOProducts, useSOCustomers } from "../hooks/use-sales-orders"
import type { SalesOrderCreatePayload } from "../types/sales.types"

export function SOCreatePage() {
  const router = useRouter()
  const createMutation = useCreateSalesOrder()
  const { data: productData, isLoading: productsLoading } = useSOProducts()
  const { data: customerData, isLoading: customersLoading } = useSOCustomers()

  const products = productData?.results ?? []
  const customers = customerData?.results ?? []

  function handleSubmit(payload: SalesOrderCreatePayload) {
    createMutation.mutate(payload, {
      onSuccess: (so) => {
        toast.success(`Sales order "${so.order_number}" created`)
        router.push("/sales/orders")
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? "Failed to create sales order"
        toast.error(message)
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="New Sales Order"
        description="Create a new sales order with line items"
      />
      <SOForm
        products={products}
        productsLoading={productsLoading}
        customers={customers}
        customersLoading={customersLoading}
        onSubmit={handleSubmit}
        isSubmitting={createMutation.isPending}
        onCancel={() => router.push("/sales/orders")}
      />
    </div>
  )
}
