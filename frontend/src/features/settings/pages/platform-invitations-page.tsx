"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { DataTable } from "@/components/data-table/data-table"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  usePlatformInvitations,
  usePlatformCancelInvitation,
  usePlatformResendInvitation,
} from "../hooks/use-invitations"
import { usePlatformTenants } from "../hooks/use-platform-users"
import { getPlatformInvitationColumns } from "../components/platform-invitation-columns"
import type { PlatformInvitation, PlatformInvitationListParams } from "../types/settings.types"

const STATUS_OPTIONS = [
  { value: "pending", label: "Pending" },
  { value: "accepted", label: "Accepted" },
  { value: "cancelled", label: "Cancelled" },
  { value: "expired", label: "Expired" },
]

export function PlatformInvitationsPage() {
  const { data: tenants = [] } = usePlatformTenants()

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 25,
  })
  const [statusFilter, setStatusFilter] = React.useState<string>("all")
  const [tenantFilter, setTenantFilter] = React.useState<string>("all")
  const [dateFrom, setDateFrom] = React.useState("")
  const [dateTo, setDateTo] = React.useState("")

  const params = React.useMemo<PlatformInvitationListParams>(() => {
    const p: PlatformInvitationListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      ordering: "-created_at",
    }
    if (statusFilter && statusFilter !== "all") p.status = statusFilter as PlatformInvitationListParams["status"]
    if (tenantFilter && tenantFilter !== "all") p.tenant = Number(tenantFilter)
    if (dateFrom) p.date_from = dateFrom
    if (dateTo) p.date_to = dateTo
    return p
  }, [pagination.pageIndex, pagination.pageSize, statusFilter, tenantFilter, dateFrom, dateTo])

  const { data, isLoading } = usePlatformInvitations(params)
  const cancelMutation = usePlatformCancelInvitation()
  const resendMutation = usePlatformResendInvitation()

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const handleCancel = React.useCallback(
    (invitation: PlatformInvitation) => {
      cancelMutation.mutate(invitation.id, {
        onSuccess: () => toast.success("Invitation cancelled"),
        onError: () => toast.error("Failed to cancel invitation"),
      })
    },
    [cancelMutation]
  )

  const handleResend = React.useCallback(
    (invitation: PlatformInvitation) => {
      resendMutation.mutate(invitation.id, {
        onSuccess: () => toast.success("Invitation resent successfully"),
        onError: () => toast.error("Failed to resend invitation"),
      })
    },
    [resendMutation]
  )

  const columns = React.useMemo(
    () =>
      getPlatformInvitationColumns({
        onCancel: handleCancel,
        onResend: handleResend,
        isCancelling: cancelMutation.isPending,
        isResending: resendMutation.isPending,
      }),
    [handleCancel, handleResend, cancelMutation.isPending, resendMutation.isPending]
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Invitations"
        description="All tenant invitations across the platform. Superuser only."
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        emptyMessage="No invitations found."
        filterContent={
          <div className="flex flex-wrap items-center gap-2">
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
              <SelectTrigger className="h-8 w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={tenantFilter} onValueChange={(v) => setTenantFilter(v ?? "all")}>
              <SelectTrigger className="h-8 w-[180px]">
                <SelectValue placeholder="Tenant" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All tenants</SelectItem>
                {tenants.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>
                    {t.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-8 w-[150px]"
              placeholder="From"
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-8 w-[150px]"
              placeholder="To"
            />
          </div>
        }
      />
    </div>
  )
}
