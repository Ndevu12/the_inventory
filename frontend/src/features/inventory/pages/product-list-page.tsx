"use client"

import { useCallback, useMemo } from "react"
import { useTranslations } from "next-intl"
import { Link } from "@/i18n/navigation"
import { PlusIcon } from "lucide-react"
import type { PaginationState } from "@tanstack/react-table"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { ProductTable } from "../components/products/product-table"
import { useProducts, useDeleteProduct } from "../hooks/use-products"
import { useCategories } from "../hooks/use-categories"
import { useProductFiltersStore } from "../stores/product-filters-store"
import { ACTIVE_STATUS_VALUES } from "../helpers/inventory-constants"

export function ProductListPage() {
  const t = useTranslations("Inventory")
  const {
    search,
    category,
    isActive,
    page,
    pageSize,
    ordering,
    setSearch,
    setCategory,
    setIsActive,
    setPage,
    setPageSize,
  } = useProductFiltersStore()

  const { data, isLoading } = useProducts({
    page,
    page_size: pageSize,
    search: search || undefined,
    category: category || undefined,
    is_active: isActive || undefined,
    ordering,
  })

  const { data: categoriesData } = useCategories({ is_active: "true" })
  const deleteMutation = useDeleteProduct()

  const pagination: PaginationState = {
    pageIndex: page - 1,
    pageSize,
  }

  const handlePaginationChange = useCallback(
    (next: PaginationState) => {
      setPage(next.pageIndex + 1)
      setPageSize(next.pageSize)
    },
    [setPage, setPageSize],
  )

  const pageCount = data ? Math.ceil(data.count / pageSize) : 0

  const categoryFilterItems = useMemo(
    () => [
      { value: "__all__", label: t("filters.allCategories") },
      ...(categoriesData?.results.map((cat) => ({
        value: String(cat.id),
        label: cat.name,
      })) ?? []),
    ],
    [categoriesData, t],
  )

  const statusFilterItems = useMemo(
    () => [
      { value: "__all__", label: t("filters.allStatus") },
      ...ACTIVE_STATUS_VALUES.map((val) => ({
        value: val,
        label:
          val === "true" ? t("shared.active") : t("shared.inactive"),
      })),
    ],
    [t],
  )

  const filterContent = (
    <div className="flex items-center gap-2">
      <Select
        items={categoryFilterItems}
        value={category || "__all__"}
        onValueChange={(val) => setCategory(val === "__all__" ? "" : (val ?? ""))}
      >
        <SelectTrigger size="sm" className="h-8 w-[150px]">
          <SelectValue placeholder={t("filters.category")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">{t("filters.allCategories")}</SelectItem>
          {categoriesData?.results.map((cat) => (
            <SelectItem key={cat.id} value={String(cat.id)}>
              {cat.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        items={statusFilterItems}
        value={isActive || "__all__"}
        onValueChange={(val) => setIsActive(val === "__all__" ? "" : (val ?? ""))}
      >
        <SelectTrigger size="sm" className="h-8 w-[120px]">
          <SelectValue placeholder={t("filters.status")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">{t("filters.allStatus")}</SelectItem>
          {ACTIVE_STATUS_VALUES.map((val) => (
            <SelectItem key={val} value={val}>
              {val === "true" ? t("shared.active") : t("shared.inactive")}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("products.title")}
        description={t("products.description")}
        actions={
          <Button asChild>
            <Link href="/products/new">
              <PlusIcon className="mr-2 size-4" />
              {t("products.addProduct")}
            </Link>
          </Button>
        }
      />

      <ProductTable
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={handlePaginationChange}
        searchValue={search}
        onSearchChange={setSearch}
        filterContent={filterContent}
        isLoading={isLoading}
        onDelete={(id) => deleteMutation.mutate(id)}
      />
    </div>
  )
}
