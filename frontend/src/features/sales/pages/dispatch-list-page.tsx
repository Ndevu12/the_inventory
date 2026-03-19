"use client"

import * as React from "react"
import Link from "next/link"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { DispatchTable } from "../components/dispatches/dispatch-table"
import { getDispatchColumns } from "../components/dispatch-columns"
import {
  useDispatches,
  useProcessDispatch,
  useDeleteDispatch,
} from "../hooks/use-dispatches"
import { DISPATCH_PROCESSED_OPTIONS } from "../helpers/dispatch-constants"
import type { Dispatch, DispatchListParams } from "../types/dispatch.types"

export function DispatchListPage() {
  const processMutation = useProcessDispatch()
  const deleteMutation = useDeleteDispatch()

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "dispatch_date", desc: true },
  ])
  const [processedFilter, setProcessedFilter] = React.useState<string[]>([])

  const params = React.useMemo<DispatchListParams>(() => {
    const p: DispatchListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
    }

    if (sorting.length > 0) {
      const s = sorting[0]
      p.ordering = s.desc ? `-${s.id}` : s.id
    }

    if (processedFilter.length === 1) {
      p.is_processed = processedFilter[0]
    }

    return p
  }, [pagination, sorting, processedFilter])

  const { data, isLoading } = useDispatches(params)

  const handleView = React.useCallback((_dispatch: Dispatch) => {
    // detail view can be added later
  }, [])

  const handleProcess = React.useCallback(
    (dispatch: Dispatch) => {
      if (
        !confirm(
          `Process dispatch "${dispatch.dispatch_number}"? This will create stock movements and cannot be undone.`,
        )
      )
        return
      processMutation.mutate(dispatch.id, {
        onSuccess: () =>
          toast.success(
            `Dispatch "${dispatch.dispatch_number}" processed — stock movements created`,
          ),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ??
            "Failed to process dispatch"
          toast.error(message)
        },
      })
    },
    [processMutation],
  )

  const handleDelete = React.useCallback(
    (dispatch: Dispatch) => {
      if (!confirm(`Delete dispatch "${dispatch.dispatch_number}"?`)) return
      deleteMutation.mutate(dispatch.id, {
        onSuccess: () =>
          toast.success(`Dispatch "${dispatch.dispatch_number}" deleted`),
        onError: () => toast.error("Failed to delete dispatch"),
      })
    },
    [deleteMutation],
  )

  const columns = React.useMemo(
    () => getDispatchColumns({ onView: handleView, onProcess: handleProcess, onDelete: handleDelete }),
    [handleView, handleProcess, handleDelete],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const fakeColumn = React.useMemo(
    () =>
      ({
        id: "is_processed",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => processedFilter,
        setFilterValue: (val: unknown) => {
          setProcessedFilter((val as string[] | undefined) ?? [])
        },
      }) as never,
    [processedFilter],
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Dispatches"
        description="Manage and process dispatches for sales orders"
        actions={
          <Button render={<Link href="/sales/dispatches/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            New Dispatch
          </Button>
        }
      />

      <DispatchTable
        columns={columns}
        data={data?.results ?? []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        filterContent={
          <DataTableFacetedFilter
            column={fakeColumn}
            title="Status"
            options={DISPATCH_PROCESSED_OPTIONS}
          />
        }
      />
    </div>
  )
}
