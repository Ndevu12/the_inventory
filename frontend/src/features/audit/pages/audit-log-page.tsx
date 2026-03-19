"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
import { DownloadIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { useAuditLog } from "../hooks/use-audit"
import { useAuditFiltersStore } from "../stores/audit-filters-store"
import { exportAuditCsv } from "../api/audit-api"
import { AuditTable } from "../components/audit-table"
import { AuditDetailDialog } from "../components/audit-detail-dialog"
import type { AuditEntry, AuditListParams } from "../types/audit.types"

export function AuditLogPage() {
  const filters = useAuditFiltersStore()

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: filters.pageSize,
  })

  const [actionFilter, setActionFilter] = React.useState<string[]>(
    filters.action ? [filters.action] : [],
  )

  const [selectedEntry, setSelectedEntry] = React.useState<AuditEntry | null>(
    null,
  )
  const [detailOpen, setDetailOpen] = React.useState(false)

  const params = React.useMemo<AuditListParams>(() => {
    const p: AuditListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      ordering: filters.ordering,
    }
    if (actionFilter.length === 1) p.action = actionFilter[0]
    if (filters.dateFrom) p.date_from = filters.dateFrom
    if (filters.dateTo) p.date_to = filters.dateTo
    return p
  }, [pagination, filters.ordering, actionFilter, filters.dateFrom, filters.dateTo])

  const { data, isLoading } = useAuditLog(params)
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const handleViewDetails = React.useCallback((entry: AuditEntry) => {
    setSelectedEntry(entry)
    setDetailOpen(true)
  }, [])

  const handleActionFilterChange = React.useCallback(
    (values: string[]) => {
      setActionFilter(values)
      filters.setAction(values.length === 1 ? values[0] : "")
    },
    [filters],
  )

  const handleExportCsv = React.useCallback(() => {
    try {
      const url = exportAuditCsv(params)
      window.open(url, "_blank")
    } catch {
      toast.error("Failed to export CSV")
    }
  }, [params])

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Audit Log"
        description="Compliance audit trail for regulatory and operational tracking."
        actions={
          <Button variant="outline" onClick={handleExportCsv}>
            <DownloadIcon className="mr-2 size-4" />
            Export CSV
          </Button>
        }
      />

      <AuditTable
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        actionFilter={actionFilter}
        onActionFilterChange={handleActionFilterChange}
        dateFrom={filters.dateFrom}
        onDateFromChange={filters.setDateFrom}
        dateTo={filters.dateTo}
        onDateToChange={filters.setDateTo}
        onViewDetails={handleViewDetails}
      />

      <AuditDetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        entry={selectedEntry}
      />
    </div>
  )
}
