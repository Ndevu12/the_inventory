"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { DownloadIcon, FileSpreadsheetIcon } from "lucide-react"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

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
import { usePlatformAuditLog } from "../hooks/use-audit"
import {
  triggerPlatformAuditExport,
} from "../api/audit-api"
import { usePlatformTenants } from "@/features/settings/hooks/use-platform-users"
import { AuditDetailDialog } from "../components/audit-detail-dialog"
import { getPlatformAuditColumns } from "../components/platform-audit-columns"
import { getAuditActionFilterOptions } from "../helpers/audit-constants"
import type {
  PlatformAuditEntry,
  PlatformAuditListParams,
} from "../types/audit.types"
import type { AuditColumnLabels } from "../components/audit-columns"

export function PlatformAuditLogPage() {
  const tPage = useTranslations("Audit.platformPage")
  const tCols = useTranslations("Audit.columns")
  const tAudit = useTranslations("Audit")
  const tFilters = useTranslations("Audit.filters")
  const tActions = useTranslations("Audit.actionLabels")
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
      toast.success(tPage("exportCsvSuccess"))
    } catch {
      toast.error(tPage("exportCsvFailed"))
    } finally {
      setExporting(null)
    }
  }, [params, tPage])

  const handleExportExcel = React.useCallback(async () => {
    setExporting("xlsx")
    try {
      await triggerPlatformAuditExport("xlsx", params)
      toast.success(tPage("exportExcelSuccess"))
    } catch {
      toast.error(tPage("exportExcelFailed"))
    } finally {
      setExporting(null)
    }
  }, [params, tPage])

  const columnLabels = React.useMemo<
    AuditColumnLabels & { tenant: string }
  >(
    () => ({
      timestamp: tCols("timestamp"),
      action: tCols("action"),
      product: tCols("product"),
      user: tCols("user"),
      ipAddress: tCols("ipAddress"),
      tenant: tCols("tenant"),
      view: tCols("view"),
      system: tAudit("system"),
      emDash: tAudit("emDash"),
    }),
    [tCols, tAudit],
  )

  const columns = React.useMemo(
    () =>
      getPlatformAuditColumns({
        onViewDetails: handleViewDetails,
        labels: columnLabels,
      }),
    [handleViewDetails, columnLabels],
  )

  const actionOptions = React.useMemo(
    () => getAuditActionFilterOptions((action) => tActions(action)),
    [tActions],
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
        title={tPage("title")}
        description={tPage("description")}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleExportCsv}
              disabled={!!exporting}
            >
              <DownloadIcon className="mr-2 size-4" />
              {tPage("exportCsv")}
            </Button>
            <Button
              variant="outline"
              onClick={handleExportExcel}
              disabled={!!exporting}
            >
              <FileSpreadsheetIcon className="mr-2 size-4" />
              {tPage("exportExcel")}
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
        emptyMessage={tPage("empty")}
        filterContent={
          <div className="flex flex-wrap items-center gap-2">
            <DataTableFacetedFilter
              column={fakeActionColumn}
              title={tFilters("actionType")}
              options={actionOptions}
            />
            <Select
              value={tenantFilter || "all"}
              onValueChange={(value) => setTenantFilter(value as string)}
            >
              <SelectTrigger className="h-8 w-[180px]">
                <SelectValue placeholder={tPage("tenantPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{tPage("allTenants")}</SelectItem>
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
              placeholder={tFilters("fromDate")}
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-8 w-[150px]"
              placeholder={tFilters("toDate")}
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
