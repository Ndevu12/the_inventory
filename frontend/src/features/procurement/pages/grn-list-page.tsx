"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import type { PaginationState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
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
import {
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table/data-table-faceted-filter"
import { GRNTable } from "../components/grn/grn-table"
import { useGRNs, useReceiveGRN, useDeleteGRN } from "../hooks/use-grn"
import { getGRNColumns } from "../components/grn-columns"
import { GRN_IS_PROCESSED_FILTER_VALUES } from "../helpers/grn-constants"
import type { GoodsReceivedNote, GRNListParams } from "../types/grn.types"

type GrnListDialog =
  | { kind: "receive"; grn: GoodsReceivedNote }
  | { kind: "delete"; grn: GoodsReceivedNote }

export function GRNListPage() {
  const locale = useLocale()
  const t = useTranslations("Procurement.grn.list")
  const tCol = useTranslations("Procurement.grn.columns")
  const tAct = useTranslations("Procurement.grn.actions")
  const tProc = useTranslations("Procurement.grnProcessStatus")
  const tShared = useTranslations("Procurement.shared")
  const tTable = useTranslations("Inventory.tableActions")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [processedFilter, setProcessedFilter] = React.useState<string[]>([])

  const processedFilterOptions: FacetedFilterOption[] = React.useMemo(
    () =>
      [...GRN_IS_PROCESSED_FILTER_VALUES].map((v) => ({
        value: v,
        label: v === "false" ? tProc("pending") : tProc("processed"),
      })),
    [tProc],
  )

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

  const [actionDialog, setActionDialog] = React.useState<GrnListDialog | null>(
    null,
  )

  const handleView = React.useCallback(() => {
    // detail view can be added later
  }, [])

  const handleReceive = React.useCallback((grn: GoodsReceivedNote) => {
    setActionDialog({ kind: "receive", grn })
  }, [])

  const handleDelete = React.useCallback((grn: GoodsReceivedNote) => {
    setActionDialog({ kind: "delete", grn })
  }, [])

  const runReceiveFromDialog = React.useCallback(() => {
    if (!actionDialog || actionDialog.kind !== "receive") return
    const grn = actionDialog.grn
    receiveMutation.mutate(grn.id, {
      onSuccess: () => {
        toast.success(t("toastProcessed", { grnNumber: grn.grn_number }))
        setActionDialog(null)
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? t("toastProcessFailed")
        toast.error(message)
      },
    })
  }, [actionDialog, receiveMutation, t])

  const runDeleteFromDialog = React.useCallback(() => {
    if (!actionDialog || actionDialog.kind !== "delete") return
    const grn = actionDialog.grn
    deleteMutation.mutate(grn.id, {
      onSuccess: () => {
        toast.success(t("toastDeleted", { grnNumber: grn.grn_number }))
        setActionDialog(null)
      },
      onError: () => toast.error(t("toastDeleteFailed")),
    })
  }, [actionDialog, deleteMutation, t])

  const dialogPending =
    (actionDialog?.kind === "receive" && receiveMutation.isPending) ||
    (actionDialog?.kind === "delete" && deleteMutation.isPending)

  const runDialogAction = React.useCallback(() => {
    if (actionDialog?.kind === "receive") runReceiveFromDialog()
    else if (actionDialog?.kind === "delete") runDeleteFromDialog()
  }, [actionDialog, runReceiveFromDialog, runDeleteFromDialog])

  const columns = React.useMemo(
    () =>
      getGRNColumns(
        { onView: handleView, onReceive: handleReceive, onDelete: handleDelete },
        {
          tColumns: (key) => tCol(key),
          emDash: tShared("emDash"),
          processedLabel: tProc("processed"),
          pendingLabel: tProc("pending"),
          viewLabel: tAct("view"),
          receiveGoodsLabel: tAct("receiveGoods"),
          deleteLabel: tTable("delete"),
          locale,
        },
      ),
    [
      handleView,
      handleReceive,
      handleDelete,
      tCol,
      tShared,
      tProc,
      tAct,
      tTable,
      locale,
    ],
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
      title={t("statusFilter")}
      options={processedFilterOptions}
    />
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("title")}
        description={t("description")}
        actions={
          <Button
            nativeButton={false}
            render={<Link href="/procurement/goods-received/new" />}
          >
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("newButton")}
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

      <AlertDialog
        open={actionDialog != null}
        onOpenChange={(open) => {
          if (!open) setActionDialog(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionDialog?.kind === "receive"
                ? tAct("receiveGoods")
                : actionDialog?.kind === "delete"
                  ? tTable("delete")
                  : ""}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionDialog?.kind === "receive"
                ? t("processConfirm", {
                    grnNumber: actionDialog.grn.grn_number,
                  })
                : actionDialog?.kind === "delete"
                  ? t("deleteConfirm", {
                      grnNumber: actionDialog.grn.grn_number,
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
                actionDialog?.kind === "delete" ? "destructive" : "default"
              }
              onClick={runDialogAction}
              disabled={dialogPending}
            >
              {dialogPending
                ? tCommonStates("loading")
                : actionDialog?.kind === "receive"
                  ? tAct("receiveGoods")
                  : actionDialog?.kind === "delete"
                    ? tTable("delete")
                    : ""}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
