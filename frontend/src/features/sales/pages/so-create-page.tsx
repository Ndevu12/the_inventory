"use client"

import { useRouter } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import type { ApiError } from "@/types/api-common"
import { SOForm } from "../components/sales-orders/so-form"
import {
  useCreateSalesOrder,
  useSOProducts,
  useSOCustomers,
} from "../hooks/use-sales-orders"
import type { SalesOrderCreatePayload } from "../types/sales.types"

export function SOCreatePage() {
  const router = useRouter()
  const t = useTranslations("Sales.salesOrders.create")
  const createMutation = useCreateSalesOrder()
  const { data: productData, isLoading: productsLoading } = useSOProducts()
  const { data: customerData, isLoading: customersLoading } = useSOCustomers()

  const products = productData?.results ?? []
  const customers = customerData?.results ?? []

  function handleSubmit(payload: SalesOrderCreatePayload) {
    createMutation.mutate(payload, {
      onSuccess: (so) => {
        toast.success(t("toastCreated", { orderNumber: so.order_number }))
        router.push("/sales/sales-orders")
      },
      onError: (error: unknown) => {
        const e = error as unknown as ApiError
        toast.error(e.message || t("toastCreateFailed"))
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />
      <SOForm
        products={products}
        productsLoading={productsLoading}
        customers={customers}
        customersLoading={customersLoading}
        onSubmit={handleSubmit}
        isSubmitting={createMutation.isPending}
        onCancel={() => router.push("/sales/sales-orders")}
      />
    </div>
  )
}
