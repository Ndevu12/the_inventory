"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useRouter } from "@/i18n/navigation"

import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"

import { ProductForm } from "../components/products/product-form"
import { useProduct, useUpdateProduct } from "../hooks/use-products"
import { useCategories } from "../hooks/use-categories"
import type { ProductSchemaValues } from "../helpers/product-schemas"

interface ProductEditPageProps {
  params: Promise<{ id: string }>
}

export function ProductEditPage({ params }: ProductEditPageProps) {
  const t = useTranslations("Inventory")
  const { id } = use(params)
  const productId = Number(id)
  const router = useRouter()

  const { data: product, isLoading } = useProduct(productId)
  const updateMutation = useUpdateProduct(productId)
  const { data: categoriesData } = useCategories({ is_active: "true" })

  function handleSubmit(data: ProductSchemaValues) {
    updateMutation.mutate(data, {
      onSuccess: () => router.push(`/products/${productId}`),
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("products.notFoundTitle")} />
        <p className="text-muted-foreground">
          {t("products.notFoundBody")}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("products.editTitle", { name: product.name })}
        description={t("products.editDescription")}
      />
      <div className="mx-auto max-w-2xl">
        <ProductForm
          initialData={product}
          categories={categoriesData?.results ?? []}
          onSubmit={handleSubmit}
          isSubmitting={updateMutation.isPending}
        />
      </div>
    </div>
  )
}
