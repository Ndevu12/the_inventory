"use client"

import * as React from "react"
import Link from "next/link"
import type { PaginationState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import {
  DataTableFacetedFilter,
} from "@/components/data-table/data-table-faceted-filter"
import { GRNTable } from "../components/grn/grn-table"
import { useGRNs, useReceiveGRN, useDeleteGRN } from "../hooks/use-grn"
import { getGRNColumns } from "../components/grn-columns"
import { GRN_PROCESSED_OPTIONS } from "../helpers/grn-constants"
import type { GoodsReceivedNote, GRNListParams } from "../types/grn.types"

export function GRNListPage() {
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [processedFilter, setProcessedFilter] = React.useState<string[]>([])

  const params = React.useMemo<GRNListParams>(() => {
    const p: GRNListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      ordering: "-received_date",
    }

    if (processedFilter.length === 1) {
      p.is_processed = processedFilter[0]
    }

    return p
  }, [pagination, processedFilter])

  const { data, isLoading } = useGRNs(params)
  const receiveMutation = useReceiveGRN()
  const deleteMutation = useDeleteGRN()

  const handleView = React.useCallback((_grn: GoodsReceivedNote) => {
    // detail view can be added later
  }, [])

  const handleReceive = React.useCallback(
    (grn: GoodsReceivedNote) => {
      if (
        !confirm(
          `Process GRN "${grn.grn_number}"? This will create stock movements and cannot be undone.`,
        )
      )
        return
      receiveMutation.mutate(grn.id, {
        onSuccess: () =>
          toast.success(
            `GRN "${grn.grn_number}" processed — stock movements created`,
          ),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ??
            "Failed to process GRN"
          toast.error(message)
        },
      })
    },
    [receiveMutation],
  )

  const handleDelete = React.useCallback(
    (grn: GoodsReceivedNote) => {
      if (!confirm(`Delete GRN "${grn.grn_number}"?`)) return
      deleteMutation.mutate(grn.id, {
        onSuccess: () => toast.success(`GRN "${grn.grn_number}" deleted`),
        onError: () => toast.error("Failed to delete GRN"),
      })
    },
    [deleteMutation],
  )

  const columns = React.useMemo(
    () => getGRNColumns({ onView: handleView, onReceive: handleReceive, onDelete: handleDelete }),
    [handleView, handleReceive, handleDelete],
  )

  const grns = data?.results ?? []
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

  const filterContent = (
    <DataTableFacetedFilter
      column={fakeColumn}
      title="Status"
      options={GRN_PROCESSED_OPTIONS}
    />
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Goods Received Notes"
        description="Track and process goods received against purchase orders"
        actions={
          <Button render={<Link href="/procurement/goods-received/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            New GRN
          </Button>
        }
      />

      <GRNTable
        columns={columns}
        data={grns}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
        filterContent={filterContent}
      />
    </div>
  )
}
