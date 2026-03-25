"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { useLocale, useTranslations } from "next-intl"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { DataTableFacetedFilter } from "@/components/data-table/data-table-faceted-filter"
import { SOTable } from "../components/sales-orders/so-table"
import { getSOColumns } from "../components/so-columns"
import {
  useSalesOrders,
  useConfirmSalesOrder,
  useCancelSalesOrder,
  useDeleteSalesOrder,
} from "../hooks/use-sales-orders"
import { SO_STATUS_FILTER_VALUES } from "../helpers/sales-constants"
import type { ApiError } from "@/types/api-common"
import type { SalesOrder, SalesOrderListParams } from "../types/sales.types"

type SOListDialog =
  | { kind: "confirm"; so: SalesOrder }
  | { kind: "cancel"; so: SalesOrder }
  | { kind: "delete"; so: SalesOrder }

export function SOListPage() {
  const router = useRouter()
  const locale = useLocale()
  const t = useTranslations("Sales.salesOrders.list")
  const tCol = useTranslations("Sales.salesOrders.columns")
  const tAct = useTranslations("Sales.salesOrders.actions")
  const tSoStatus = useTranslations("Sales.soStatus")
  const tShared = useTranslations("Sales.shared")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")

  const confirmMutation = useConfirmSalesOrder()
  const cancelMutation = useCancelSalesOrder()
  const deleteMutation = useDeleteSalesOrder()

  const [actionDialog, setActionDialog] = React.useState<SOListDialog | null>(
    null,
  )

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
      router.push(`/sales/sales-orders/${so.id}`)
    },
    [router],
  )

  const handleConfirm = React.useCallback((so: SalesOrder) => {
    setActionDialog({ kind: "confirm", so })
  }, [])

  const handleCancel = React.useCallback((so: SalesOrder) => {
    setActionDialog({ kind: "cancel", so })
  }, [])

  const handleDelete = React.useCallback((so: SalesOrder) => {
    setActionDialog({ kind: "delete", so })
  }, [])

  const runDialogAction = React.useCallback(() => {
    if (!actionDialog) return
    const { kind, so } = actionDialog
    if (kind === "confirm") {
      confirmMutation.mutate(so.id, {
        onSuccess: () => {
          toast.success(
            t("toastConfirmed", { orderNumber: so.order_number }),
          )
          setActionDialog(null)
        },
        onError: (error: unknown) => {
          const e = error as unknown as ApiError
          toast.error(e.message || t("confirmFailed"))
        },
      })
      return
    }
    if (kind === "cancel") {
      cancelMutation.mutate(so.id, {
        onSuccess: () => {
          toast.success(
            t("toastCancelled", { orderNumber: so.order_number }),
          )
          setActionDialog(null)
        },
        onError: (error: unknown) => {
          const e = error as unknown as ApiError
          toast.error(e.message || t("cancelFailed"))
        },
      })
      return
    }
    deleteMutation.mutate(so.id, {
      onSuccess: () => {
        toast.success(t("toastDeleted", { orderNumber: so.order_number }))
        setActionDialog(null)
      },
      onError: (error: unknown) => {
        const e = error as unknown as ApiError
        toast.error(e.message || t("deleteFailed"))
      },
    })
  }, [
    actionDialog,
    confirmMutation,
    cancelMutation,
    deleteMutation,
    t,
  ])

  const dialogPending =
    (actionDialog?.kind === "confirm" && confirmMutation.isPending) ||
    (actionDialog?.kind === "cancel" && cancelMutation.isPending) ||
    (actionDialog?.kind === "delete" && deleteMutation.isPending)

  const columnLabels = React.useMemo(
    () => ({
      tColumns: (key: string) => tCol(key),
      emDash: tShared("emDash"),
      viewLabel: tAct("view"),
      confirmLabel: tAct("confirm"),
      cancelLabel: tAct("cancel"),
      deleteLabel: tAct("delete"),
      locale,
    }),
    [tCol, tShared, tAct, locale],
  )

  const columns = React.useMemo(
    () =>
      getSOColumns(
        {
          onView: handleView,
          onConfirm: handleConfirm,
          onCancel: handleCancel,
          onDelete: handleDelete,
        },
        columnLabels,
      ),
    [handleView, handleConfirm, handleCancel, handleDelete, columnLabels],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const statusFilterOptions = React.useMemo(
    () =>
      SO_STATUS_FILTER_VALUES.map((value) => ({
        value,
        label: tSoStatus(value),
      })),
    [tSoStatus],
  )

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
        title={t("title")}
        description={t("description")}
        actions={
          <Button render={<Link href="/sales/sales-orders/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("newButton")}
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
            title={t("statusFilter")}
            options={statusFilterOptions}
          />
        }
      />

      <AlertDialog
        open={actionDialog != null}
        onOpenChange={(open) => {
          if (!open) setActionDialog(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionDialog?.kind === "confirm"
                ? tAct("confirm")
                : actionDialog?.kind === "cancel"
                  ? tAct("cancel")
                  : actionDialog?.kind === "delete"
                    ? tAct("delete")
                    : ""}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionDialog?.kind === "confirm"
                ? t("confirmPrompt", {
                    orderNumber: actionDialog.so.order_number,
                  })
                : actionDialog?.kind === "cancel"
                  ? t("cancelPrompt", {
                      orderNumber: actionDialog.so.order_number,
                    })
                  : actionDialog?.kind === "delete"
                    ? t("deletePrompt", {
                        orderNumber: actionDialog.so.order_number,
                      })
                    : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={dialogPending}>
              {tCommon("cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              variant={
                actionDialog?.kind === "confirm" ? "default" : "destructive"
              }
              onClick={runDialogAction}
              disabled={dialogPending}
            >
              {dialogPending
                ? tCommonStates("loading")
                : actionDialog?.kind === "confirm"
                  ? tAct("confirm")
                  : actionDialog?.kind === "cancel"
                    ? tAct("cancel")
                    : actionDialog?.kind === "delete"
                      ? tAct("delete")
                      : ""}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
