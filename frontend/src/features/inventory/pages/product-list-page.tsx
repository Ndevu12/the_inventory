"use client"

import { useCallback } from "react"
import Link from "next/link"
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
import { ACTIVE_STATUS_OPTIONS } from "../helpers/inventory-constants"

export function ProductListPage() {
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

  const filterContent = (
    <div className="flex items-center gap-2">
      <Select
        value={category || undefined}
        onValueChange={(val) => setCategory(val === "__all__" ? "" : (val ?? ""))}
      >
        <SelectTrigger size="sm" className="h-8 w-[150px]">
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All Categories</SelectItem>
          {categoriesData?.results.map((cat) => (
            <SelectItem key={cat.id} value={String(cat.id)}>
              {cat.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={isActive || undefined}
        onValueChange={(val) => setIsActive(val === "__all__" ? "" : (val ?? ""))}
      >
        <SelectTrigger size="sm" className="h-8 w-[120px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All Status</SelectItem>
          {ACTIVE_STATUS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Manage your product catalog"
        actions={
          <Button render={<Link href="/products/new" />}>
            <PlusIcon className="mr-2 size-4" />
            Add Product
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
