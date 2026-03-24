"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { Link } from "@/i18n/navigation"
import { PencilIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { Skeleton } from "@/components/ui/skeleton"

import { ProductDetailTabs } from "../components/products/product-detail-tabs"
import {
  useProduct,
  useProductStock,
  useProductMovements,
  useProductLots,
} from "../hooks/use-products"

interface ProductDetailPageProps {
  params: Promise<{ id: string }>
}

export function ProductDetailPage({ params }: ProductDetailPageProps) {
  const t = useTranslations("Inventory")
  const { id } = use(params)
  const productId = Number(id)

  const { data: product, isLoading } = useProduct(productId)
  const { data: stockData, isLoading: isLoadingStock } =
    useProductStock(productId)
  const { data: movementsData, isLoading: isLoadingMovements } =
    useProductMovements(productId)
  const { data: lotsData, isLoading: isLoadingLots } =
    useProductLots(productId)

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
        title={product.name}
        description={t("products.detailSku", { sku: product.sku })}
        actions={
          <Button variant="outline" render={<Link href={`/products/${productId}/edit`} />}>
            <PencilIcon className="mr-2 size-4" />
            {t("products.detailEdit")}
          </Button>
        }
      />

      <ProductDetailTabs
        product={product}
        stockRecords={stockData?.results}
        movements={movementsData?.results}
        lots={lotsData?.results}
        isLoadingStock={isLoadingStock}
        isLoadingMovements={isLoadingMovements}
        isLoadingLots={isLoadingLots}
      />
    </div>
  )
}
