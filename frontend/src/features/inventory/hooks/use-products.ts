"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  fetchProducts,
  fetchProduct,
  createProduct,
  updateProduct,
  deleteProduct,
  fetchProductStock,
  fetchProductMovements,
  fetchProductLots,
  type ProductListParams,
} from "../api/products-api"
import type { ProductFormValues } from "../types/inventory.types"

export const productKeys = {
  all: ["products"] as const,
  lists: () => [...productKeys.all, "list"] as const,
  list: (params?: ProductListParams) =>
    [...productKeys.lists(), params] as const,
  details: () => [...productKeys.all, "detail"] as const,
  detail: (id: number) => [...productKeys.details(), id] as const,
  stock: (id: number) => [...productKeys.detail(id), "stock"] as const,
  movements: (id: number) =>
    [...productKeys.detail(id), "movements"] as const,
  lots: (id: number) => [...productKeys.detail(id), "lots"] as const,
}

export function useProducts(params?: ProductListParams) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: () => fetchProducts(params),
  })
}

export function useAllProducts() {
  return useQuery({
    queryKey: [...productKeys.all, "all"],
    queryFn: () => fetchProducts({ page_size: 1000 }),
    select: (data) => data.results,
    staleTime: 5 * 60 * 1000,
  })
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: productKeys.detail(id),
    queryFn: () => fetchProduct(id),
    enabled: id > 0,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ProductFormValues) => createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
      toast.success("Product created successfully")
    },
    onError: () => {
      toast.error("Failed to create product")
    },
  })
}

export function useUpdateProduct(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<ProductFormValues>) => updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
      toast.success("Product updated successfully")
    },
    onError: () => {
      toast.error("Failed to update product")
    },
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
      toast.success("Product deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete product")
    },
  })
}

export function useProductStock(id: number) {
  return useQuery({
    queryKey: productKeys.stock(id),
    queryFn: () => fetchProductStock(id),
    enabled: id > 0,
  })
}

export function useProductMovements(id: number) {
  return useQuery({
    queryKey: productKeys.movements(id),
    queryFn: () => fetchProductMovements(id),
    enabled: id > 0,
  })
}

export function useProductLots(id: number) {
  return useQuery({
    queryKey: productKeys.lots(id),
    queryFn: () => fetchProductLots(id),
    enabled: id > 0,
  })
}
