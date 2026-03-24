"use client"

import * as React from "react"
import { Link, useRouter } from "@/i18n/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { useLocale, useTranslations } from "next-intl"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import type { ApiError } from "@/types/api-common"
import { DataTableFacetedFilter } from "@/components/data-table/data-table-faceted-filter"
import { DispatchFulfillmentDialog } from "../components/dispatches/dispatch-fulfillment-dialog"
import { DispatchTable } from "../components/dispatches/dispatch-table"
import { getDispatchColumns } from "../components/dispatch-columns"
import {
  useDispatches,
  useProcessDispatch,
  useDeleteDispatch,
} from "../hooks/use-dispatches"
import { DISPATCH_PROCESSED_FILTER_VALUES } from "../helpers/dispatch-constants"
import type { Dispatch, DispatchListParams } from "../types/dispatch.types"

export function DispatchListPage() {
  const router = useRouter()
  const locale = useLocale()
  const t = useTranslations("Sales.dispatches.list")
  const tCol = useTranslations("Sales.dispatches.columns")
  const tAct = useTranslations("Sales.dispatches.actions")
  const tProc = useTranslations("Sales.dispatchProcessed")
  const tShared = useTranslations("Sales.shared")

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
  const [fulfillmentDialog, setFulfillmentDialog] = React.useState<{
    dispatch: Dispatch
    intro?: string
  } | null>(null)

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

  const handleView = React.useCallback(
    (dispatch: Dispatch) => {
      router.push(`/sales/sales-orders/${dispatch.sales_order}`)
    },
    [router],
  )

  const handleProcess = React.useCallback(
    (dispatch: Dispatch) => {
      if (
        !confirm(
          t("processPrompt", { dispatchNumber: dispatch.dispatch_number }),
        )
      )
        return
      processMutation.mutate(
        { id: dispatch.id },
        {
          onSuccess: () =>
            toast.success(
              t("toastProcessed", {
                dispatchNumber: dispatch.dispatch_number,
              }),
            ),
          onError: (error: unknown) => {
            const e = error as unknown as ApiError
            toast.error(e.message || t("processFailed"))
            if (e.status === 400) {
              setFulfillmentDialog({
                dispatch,
                intro: e.message,
              })
            }
          },
        },
      )
    },
    [processMutation, t],
  )

  const handleReviewStock = React.useCallback((dispatch: Dispatch) => {
    setFulfillmentDialog({ dispatch })
  }, [])

  const handleDelete = React.useCallback(
    (dispatch: Dispatch) => {
      if (!confirm(t("deletePrompt", { dispatchNumber: dispatch.dispatch_number })))
        return
      deleteMutation.mutate(dispatch.id, {
        onSuccess: () =>
          toast.success(
            t("toastDeleted", { dispatchNumber: dispatch.dispatch_number }),
          ),
        onError: (error: unknown) => {
          const e = error as unknown as ApiError
          toast.error(e.message || t("deleteFailed"))
        },
      })
    },
    [deleteMutation, t],
  )

  const columnLabels = React.useMemo(
    () => ({
      tColumns: (key: string) => tCol(key),
      emDash: tShared("emDash"),
      processedLabel: tCol("processed"),
      pendingLabel: tCol("pending"),
      viewLabel: tAct("view"),
      reviewStockLabel: tAct("reviewStock"),
      processDispatchLabel: tAct("processDispatch"),
      deleteLabel: tAct("delete"),
      locale,
    }),
    [tCol, tShared, tAct, locale],
  )

  const columns = React.useMemo(
    () =>
      getDispatchColumns(
        {
          onView: handleView,
          onReviewStock: handleReviewStock,
          onProcess: handleProcess,
          onDelete: handleDelete,
        },
        columnLabels,
      ),
    [handleView, handleReviewStock, handleProcess, handleDelete, columnLabels],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const processedOptions = React.useMemo(
    () =>
      DISPATCH_PROCESSED_FILTER_VALUES.map((value) => ({
        value,
        label: value === "true" ? tProc("processed") : tProc("pending"),
      })),
    [tProc],
  )

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
        title={t("title")}
        description={t("description")}
        actions={
          <Button render={<Link href="/sales/dispatches/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("newButton")}
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
            title={t("statusFilter")}
            options={processedOptions}
          />
        }
      />

      <DispatchFulfillmentDialog
        open={fulfillmentDialog != null}
        onOpenChange={(open) => {
          if (!open) setFulfillmentDialog(null)
        }}
        dispatch={fulfillmentDialog?.dispatch ?? null}
        introText={fulfillmentDialog?.intro}
      />
    </div>
  )
}
