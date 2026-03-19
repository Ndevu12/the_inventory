import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types"
import type {
  Product,
  StockRecord,
  StockMovement,
  StockLot,
  ProductFormValues,
} from "../types/inventory.types"

export interface ProductListParams {
  page?: number
  page_size?: number
  search?: string
  category?: string
  is_active?: string
  ordering?: string
}

export function fetchProducts(
  params?: ProductListParams,
): Promise<PaginatedResponse<Product>> {
  const query: Record<string, string> = {}
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        query[key] = String(value)
      }
    }
  }
  return apiClient.get<PaginatedResponse<Product>>("/products/", query)
}

export function fetchProduct(id: number): Promise<Product> {
  return apiClient.get<Product>(`/products/${id}/`)
}

export function createProduct(data: ProductFormValues): Promise<Product> {
  return apiClient.post<Product>("/products/", data)
}

export function updateProduct(
  id: number,
  data: Partial<ProductFormValues>,
): Promise<Product> {
  return apiClient.patch<Product>(`/products/${id}/`, data)
}

export function deleteProduct(id: number): Promise<void> {
  return apiClient.delete(`/products/${id}/`)
}

export function fetchProductStock(
  id: number,
): Promise<PaginatedResponse<StockRecord>> {
  return apiClient.get<PaginatedResponse<StockRecord>>(
    `/products/${id}/stock/`,
  )
}

export function fetchProductMovements(
  id: number,
): Promise<PaginatedResponse<StockMovement>> {
  return apiClient.get<PaginatedResponse<StockMovement>>(
    `/products/${id}/movements/`,
  )
}

export function fetchProductLots(
  id: number,
): Promise<PaginatedResponse<StockLot>> {
  return apiClient.get<PaginatedResponse<StockLot>>(`/products/${id}/lots/`)
}
