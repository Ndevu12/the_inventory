import { useQuery } from "@tanstack/react-query"
import { fetchAuditLog, fetchAuditEntry } from "../api/audit-api"
import type { AuditListParams } from "../types/audit.types"

const AUDIT_KEY = "audit-log" as const

export function useAuditLog(params: AuditListParams = {}) {
  return useQuery({
    queryKey: [AUDIT_KEY, params],
    queryFn: () => fetchAuditLog(params),
  })
}

export function useAuditEntry(id: number) {
  return useQuery({
    queryKey: [AUDIT_KEY, id],
    queryFn: () => fetchAuditEntry(id),
    enabled: id > 0,
  })
}
