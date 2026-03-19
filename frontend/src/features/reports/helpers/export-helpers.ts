import { useAuthStore } from "@/lib/auth-store"
import type { ExportFormat } from "@/types/api-common"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1"

export function buildExportUrl(
  reportPath: string,
  format: ExportFormat,
  params?: Record<string, string>,
): string {
  const url = new URL(`${API_BASE}/reports/${reportPath}/`, window.location.origin)
  url.searchParams.set("export", format)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value) url.searchParams.set(key, value)
    }
  }
  return url.toString()
}

export async function triggerDownload(
  reportPath: string,
  format: ExportFormat,
  params?: Record<string, string>,
): Promise<void> {
  const url = buildExportUrl(reportPath, format, params)
  const { accessToken, tenantSlug } = useAuthStore.getState()

  const headers: HeadersInit = {}
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`
  if (tenantSlug) headers["X-Tenant"] = tenantSlug

  const res = await fetch(url, { headers })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)

  const blob = await res.blob()
  const disposition = res.headers.get("Content-Disposition")
  const filename =
    disposition?.match(/filename="?(.+?)"?$/)?.[1] ??
    `report.${format}`

  const a = document.createElement("a")
  a.href = URL.createObjectURL(blob)
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}
