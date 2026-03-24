"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import type { PaginationState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { toast } from "sonner"

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

export function GRNListPage() {
  const locale = useLocale()
  const t = useTranslations("Procurement.grn.list")
  const tCol = useTranslations("Procurement.grn.columns")
  const tAct = useTranslations("Procurement.grn.actions")
  const tProc = useTranslations("Procurement.grnProcessStatus")
  const tShared = useTranslations("Procurement.shared")
  const tTable = useTranslations("Inventory.tableActions")

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

  const handleView = React.useCallback(() => {
    // detail view can be added later
  }, [])

  const handleReceive = React.useCallback(
    (grn: GoodsReceivedNote) => {
      if (!confirm(t("processConfirm", { grnNumber: grn.grn_number }))) return
      receiveMutation.mutate(grn.id, {
        onSuccess: () =>
          toast.success(t("toastProcessed", { grnNumber: grn.grn_number })),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ?? t("toastProcessFailed")
          toast.error(message)
        },
      })
    },
    [receiveMutation, t],
  )

  const handleDelete = React.useCallback(
    (grn: GoodsReceivedNote) => {
      if (!confirm(t("deleteConfirm", { grnNumber: grn.grn_number }))) return
      deleteMutation.mutate(grn.id, {
        onSuccess: () => toast.success(t("toastDeleted", { grnNumber: grn.grn_number })),
        onError: () => toast.error(t("toastDeleteFailed")),
      })
    },
    [deleteMutation, t],
  )

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
    </div>
  )
}
