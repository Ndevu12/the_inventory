"use client"

import { useTranslations } from "next-intl"
import { useRouter } from "@/i18n/navigation"

import { PageHeader } from "@/components/layout/page-header"

import { ProductForm } from "../components/products/product-form"
import { useCreateProduct } from "../hooks/use-products"
import { useCategories } from "../hooks/use-categories"
import type { ProductSchemaValues } from "../helpers/product-schemas"

export function ProductCreatePage() {
  const t = useTranslations("Inventory")
  const router = useRouter()
  const createMutation = useCreateProduct()
  const { data: categoriesData } = useCategories({ is_active: "true" })

  function handleSubmit(data: ProductSchemaValues) {
    createMutation.mutate(data, {
      onSuccess: () => router.push("/products"),
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("products.newTitle")}
        description={t("products.newDescription")}
      />
      <div className="mx-auto max-w-2xl">
        <ProductForm
          categories={categoriesData?.results ?? []}
          onSubmit={handleSubmit}
          isSubmitting={createMutation.isPending}
        />
      </div>
    </div>
  )
}
