"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { SOTable } from "../components/sales-orders/so-table"
import { getSOColumns } from "../components/so-columns"
import {
  useSalesOrders,
  useConfirmSalesOrder,
  useCancelSalesOrder,
  useDeleteSalesOrder,
} from "../hooks/use-sales-orders"
import { SO_STATUS_OPTIONS } from "../helpers/sales-constants"
import type { SalesOrder, SalesOrderListParams } from "../types/sales.types"

export function SOListPage() {
  const router = useRouter()
  const confirmMutation = useConfirmSalesOrder()
  const cancelMutation = useCancelSalesOrder()
  const deleteMutation = useDeleteSalesOrder()

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "order_date", desc: true },
  ])
  const [statusFilter, setStatusFilter] = React.useState<string[]>([])
  const [search, setSearch] = React.useState("")

  const params = React.useMemo<SalesOrderListParams>(() => {
    const p: SalesOrderListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
    }

    if (sorting.length > 0) {
      const s = sorting[0]
      p.ordering = s.desc ? `-${s.id}` : s.id
    }

    if (statusFilter.length === 1) {
      p.status = statusFilter[0]
    }

    if (search) {
      p.search = search
    }

    return p
  }, [pagination, sorting, statusFilter, search])

  const { data, isLoading } = useSalesOrders(params)

  const handleView = React.useCallback(
    (so: SalesOrder) => {
      router.push(`/sales/orders/${so.id}`)
    },
    [router],
  )

  const handleConfirm = React.useCallback(
    (so: SalesOrder) => {
      if (!confirm(`Confirm sales order "${so.order_number}"?`)) return
      confirmMutation.mutate(so.id, {
        onSuccess: () => toast.success(`Order "${so.order_number}" confirmed`),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ?? "Failed to confirm order"
          toast.error(message)
        },
      })
    },
    [confirmMutation],
  )

  const handleCancel = React.useCallback(
    (so: SalesOrder) => {
      if (!confirm(`Cancel sales order "${so.order_number}"?`)) return
      cancelMutation.mutate(so.id, {
        onSuccess: () => toast.success(`Order "${so.order_number}" cancelled`),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ?? "Failed to cancel order"
          toast.error(message)
        },
      })
    },
    [cancelMutation],
  )

  const handleDelete = React.useCallback(
    (so: SalesOrder) => {
      if (!confirm(`Delete sales order "${so.order_number}"?`)) return
      deleteMutation.mutate(so.id, {
        onSuccess: () => toast.success(`Order "${so.order_number}" deleted`),
        onError: () => toast.error("Failed to delete order"),
      })
    },
    [deleteMutation],
  )

  const columns = React.useMemo(
    () =>
      getSOColumns({
        onView: handleView,
        onConfirm: handleConfirm,
        onCancel: handleCancel,
        onDelete: handleDelete,
      }),
    [handleView, handleConfirm, handleCancel, handleDelete],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const fakeColumn = React.useMemo(
    () =>
      ({
        id: "status",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => statusFilter,
        setFilterValue: (val: unknown) => {
          setStatusFilter((val as string[] | undefined) ?? [])
        },
      }) as never,
    [statusFilter],
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Sales Orders"
        description="Manage sales orders and track fulfillment"
        actions={
          <Button render={<Link href="/sales/orders/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            New Order
          </Button>
        }
      />

      <SOTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={search}
        onSearchChange={setSearch}
        isLoading={isLoading}
        filterContent={
          <DataTableFacetedFilter
            column={fakeColumn}
            title="Status"
            options={SO_STATUS_OPTIONS}
          />
        }
      />
    </div>
  )
}
