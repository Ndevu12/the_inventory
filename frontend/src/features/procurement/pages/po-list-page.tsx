"use client"

import { useCallback, useMemo, useState } from "react"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import {
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table/data-table-faceted-filter"

import {
  usePurchaseOrders,
  useConfirmPurchaseOrder,
  useCancelPurchaseOrder,
} from "../hooks/use-purchase-orders"
import { PO_STATUS_OPTIONS } from "../helpers/procurement-constants"
import { getPurchaseOrderColumns } from "../components/po-columns"
import { POTable } from "../components/purchase-orders/po-table"
import type { PurchaseOrder } from "../types/procurement.types"

const STATUS_FILTER_OPTIONS: FacetedFilterOption[] = PO_STATUS_OPTIONS.map((s) => ({
  label: s.label,
  value: s.value,
}))

export function POListPage() {
  const router = useRouter()

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  })
  const [sorting, setSorting] = useState<SortingState>([
    { id: "order_date", desc: true },
  ])
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")

  const ordering = useMemo(() => {
    if (sorting.length === 0) return "-order_date"
    const col = sorting[0]
    return col.desc ? `-${col.id}` : col.id
  }, [sorting])

  const { data, isLoading } = usePurchaseOrders({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    ordering,
    search: search || undefined,
    status: statusFilter || undefined,
  })

  const confirmMutation = useConfirmPurchaseOrder()
  const cancelMutation = useCancelPurchaseOrder()

  const handleView = useCallback(
    (po: PurchaseOrder) => {
      router.push(`/procurement/purchase-orders/${po.id}`)
    },
    [router],
  )

  const handleConfirm = useCallback(
    (po: PurchaseOrder) => {
      confirmMutation.mutate(po.id, {
        onSuccess: () =>
          toast.success(`Purchase order ${po.order_number} confirmed`),
        onError: (error) =>
          toast.error(
            `Failed to confirm: ${(error as { message?: string }).message ?? "Unknown error"}`,
          ),
      })
    },
    [confirmMutation],
  )

  const handleCancel = useCallback(
    (po: PurchaseOrder) => {
      if (!confirm(`Cancel purchase order "${po.order_number}"?`)) return
      cancelMutation.mutate(po.id, {
        onSuccess: () =>
          toast.success(`Purchase order ${po.order_number} cancelled`),
        onError: (error) =>
          toast.error(
            `Failed to cancel: ${(error as { message?: string }).message ?? "Unknown error"}`,
          ),
      })
    },
    [cancelMutation],
  )

  const columns = useMemo(
    () =>
      getPurchaseOrderColumns({
        onView: handleView,
        onConfirm: handleConfirm,
        onCancel: handleCancel,
      }),
    [handleView, handleConfirm, handleCancel],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Orders"
        description="Manage orders placed with suppliers."
        actions={
          <Button onClick={() => router.push("/procurement/purchase-orders/new")}>
            <PlusIcon className="mr-2 size-4" />
            New Purchase Order
          </Button>
        }
      />

      <POTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        sorting={sorting}
        onSortingChange={setSorting}
        searchValue={search}
        onSearchChange={setSearch}
        isLoading={isLoading}
        filterContent={
          <DataTableFacetedFilter
            title="Status"
            options={STATUS_FILTER_OPTIONS}
          />
        }
      />
    </div>
  )
}
