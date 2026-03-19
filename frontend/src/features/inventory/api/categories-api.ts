import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types"
import type { Category } from "../types/inventory.types"

type CategoryListParams = {
  is_active?: string
  page_size?: number | string
  search?: string
}

function toQuery(params?: CategoryListParams): Record<string, string> | undefined {
  if (!params) return undefined
  const out: Record<string, string> = {}
  if (params.search) out.search = params.search
  if (params.is_active != null) out.is_active = String(params.is_active)
  if (params.page_size != null) out.page_size = String(params.page_size)
  return Object.keys(out).length > 0 ? out : { page_size: "200" }
}

export function fetchCategories(
  params?: CategoryListParams
): Promise<PaginatedResponse<Category>> {
  const query = toQuery(params) ?? { page_size: "200" }
  return apiClient.get<PaginatedResponse<Category>>("/categories/", query)
}

export function createCategory(data: {
  name: string
  slug: string
  description: string
  is_active: boolean
}): Promise<Category> {
  return apiClient.post<Category>("/categories/", data)
}

export function updateCategory(
  id: number,
  data: { name?: string; slug?: string; description?: string; is_active?: boolean }
): Promise<Category> {
  return apiClient.patch<Category>(`/categories/${id}/`, data)
}

export function deleteCategory(id: number): Promise<void> {
  return apiClient.delete(`/categories/${id}/`)
}
