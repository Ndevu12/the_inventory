"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { DownloadIcon, FileSpreadsheetIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { DataTable } from "@/components/data-table/data-table"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEffect } from "react"
import { useRouter } from "@/i18n/navigation"
import { useAuth } from "@/features/auth/context/auth-context"
import { usePlatformAuditLog } from "../hooks/use-audit"
import {
  triggerPlatformAuditExport,
} from "../api/audit-api"
import { usePlatformTenants } from "@/features/settings/hooks/use-platform-users"
import { AuditDetailDialog } from "../components/audit-detail-dialog"
import { getPlatformAuditColumns } from "../components/platform-audit-columns"
import { AUDIT_ACTION_OPTIONS } from "../helpers/audit-constants"
import type {
  PlatformAuditEntry,
  PlatformAuditListParams,
} from "../types/audit.types"

export function PlatformAuditLogPage() {
  const { data: tenants = [] } = usePlatformTenants()

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 25,
  })

  const [actionFilter, setActionFilter] = React.useState<string[]>([])
  const [tenantFilter, setTenantFilter] = React.useState<string>("all")
  const [dateFrom, setDateFrom] = React.useState("")
  const [dateTo, setDateTo] = React.useState("")
  const [selectedEntry, setSelectedEntry] = React.useState<PlatformAuditEntry | null>(
    null,
  )
  const [detailOpen, setDetailOpen] = React.useState(false)
  const [exporting, setExporting] = React.useState<"csv" | "xlsx" | null>(null)

  const params = React.useMemo<PlatformAuditListParams>(() => {
    const p: PlatformAuditListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      ordering: "-timestamp",
    }
    if (actionFilter.length === 1) p.action = actionFilter[0]
    if (tenantFilter && tenantFilter !== "all") p.tenant = tenantFilter
    if (dateFrom) p.date_from = dateFrom
    if (dateTo) p.date_to = dateTo
    return p
  }, [
    pagination.pageIndex,
    pagination.pageSize,
    actionFilter,
    tenantFilter,
    dateFrom,
    dateTo,
  ])

  const { data, isLoading } = usePlatformAuditLog(params)
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const handleViewDetails = React.useCallback((entry: PlatformAuditEntry) => {
    setSelectedEntry(entry)
    setDetailOpen(true)
  }, [])

  const handleActionFilterChange = React.useCallback((values: string[]) => {
    setActionFilter(values)
  }, [])

  const handleExportCsv = React.useCallback(async () => {
    setExporting("csv")
    try {
      await triggerPlatformAuditExport("csv", params)
      toast.success("CSV exported successfully")
    } catch {
      toast.error("Failed to export CSV")
    } finally {
      setExporting(null)
    }
  }, [params])

  const handleExportExcel = React.useCallback(async () => {
    setExporting("xlsx")
    try {
      await triggerPlatformAuditExport("xlsx", params)
      toast.success("Excel exported successfully")
    } catch {
      toast.error("Failed to export Excel")
    } finally {
      setExporting(null)
    }
  }, [params])

  const columns = React.useMemo(
    () => getPlatformAuditColumns({ onViewDetails: handleViewDetails }),
    [handleViewDetails],
  )

  const fakeActionColumn = React.useMemo(
    () =>
      ({
        id: "action",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => actionFilter,
        setFilterValue: (val: unknown) => {
          setActionFilter((val as string[] | undefined) ?? [])
        },
      }) as never,
    [actionFilter],
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Platform Audit Log"
        description="Unified audit trail across all tenants. Superuser only."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleExportCsv}
              disabled={!!exporting}
            >
              <DownloadIcon className="mr-2 size-4" />
              Export CSV
            </Button>
            <Button
              variant="outline"
              onClick={handleExportExcel}
              disabled={!!exporting}
            >
              <FileSpreadsheetIcon className="mr-2 size-4" />
              Export Excel
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        emptyMessage="No platform audit log entries found."
        filterContent={
          <div className="flex flex-wrap items-center gap-2">
            <DataTableFacetedFilter
              column={fakeActionColumn}
              title="Action Type"
              options={AUDIT_ACTION_OPTIONS}
            />
            <Select
              value={tenantFilter || "all"}
              onValueChange={(value) => setTenantFilter(value as string)}
            >
              <SelectTrigger className="h-8 w-[180px]">
                <SelectValue placeholder="All tenants" />
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
              placeholder="From date"
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-8 w-[150px]"
              placeholder="To date"
            />
          </div>
        }
      />

      <AuditDetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        entry={selectedEntry}
      />
    </div>
  )
}
