import { useQuery } from "@tanstack/react-query"
import {
  fetchAuditLog,
  fetchAuditEntry,
  fetchPlatformAuditLog,
} from "../api/audit-api"
import type {
  AuditListParams,
  PlatformAuditListParams,
} from "../types/audit.types"

const AUDIT_KEY = "audit-log" as const
const PLATFORM_AUDIT_KEY = "platform-audit-log" as const

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

export function usePlatformAuditLog(params: PlatformAuditListParams = {}) {
  return useQuery({
    queryKey: [PLATFORM_AUDIT_KEY, params],
    queryFn: () => fetchPlatformAuditLog(params),
  })
}
