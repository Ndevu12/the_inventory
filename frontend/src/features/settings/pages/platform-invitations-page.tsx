"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

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
import type { TenantRole } from "../types/settings.types"

const STATUS_FILTER_VALUES = ["pending", "accepted", "cancelled", "expired"] as const

export function PlatformInvitationsPage() {
  const { data: tenants = [] } = usePlatformTenants()
  const t = useTranslations("SettingsPlatform.invitations")
  const tRoles = useTranslations("SettingsTenant.roles")

  const tInv = React.useCallback(
    (key: string) => t(key as Parameters<typeof t>[0]),
    [t],
  )
  const roleLabel = React.useCallback(
    (role: TenantRole) => tRoles(role),
    [tRoles],
  )

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
        onSuccess: () => toast.success(t("toast.cancelled")),
        onError: () => toast.error(t("toast.cancelFailed")),
      })
    },
    [cancelMutation, t],
  )

  const handleResend = React.useCallback(
    (invitation: PlatformInvitation) => {
      resendMutation.mutate(invitation.id, {
        onSuccess: () => toast.success(t("toast.resent")),
        onError: () => toast.error(t("toast.resendFailed")),
      })
    },
    [resendMutation, t],
  )

  const columns = React.useMemo(
    () =>
      getPlatformInvitationColumns({
        onCancel: handleCancel,
        onResend: handleResend,
        isCancelling: cancelMutation.isPending,
        isResending: resendMutation.isPending,
        t: tInv,
        roleLabel,
      }),
    [
      handleCancel,
      handleResend,
      cancelMutation.isPending,
      resendMutation.isPending,
      tInv,
      roleLabel,
    ],
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("page.title")}
        description={t("page.description")}
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        emptyMessage={t("emptyMessage")}
        filterContent={
          <div className="flex flex-wrap items-center gap-2">
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
              <SelectTrigger className="h-8 w-[140px]">
                <SelectValue placeholder={t("filterStatusPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("filterAllStatuses")}</SelectItem>
                {STATUS_FILTER_VALUES.map((value) => (
                  <SelectItem key={value} value={value}>
                    {t(`status.${value}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={tenantFilter} onValueChange={(v) => setTenantFilter(v ?? "all")}>
              <SelectTrigger className="h-8 w-[180px]">
                <SelectValue placeholder={t("filterTenantPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("filterAllTenants")}</SelectItem>
                {tenants.map((tenant) => (
                  <SelectItem key={tenant.id} value={String(tenant.id)}>
                    {tenant.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-8 w-[150px]"
              placeholder={t("filterFrom")}
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-8 w-[150px]"
              placeholder={t("filterTo")}
            />
          </div>
        }
      />
    </div>
  )
}
