"use client"

import { useCallback, useMemo, useState } from "react"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
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
import { PO_STATUS_VALUES } from "../helpers/procurement-constants"
import { getPurchaseOrderColumns } from "../components/po-columns"
import { POTable } from "../components/purchase-orders/po-table"
import type { PurchaseOrder } from "../types/procurement.types"

export function POListPage() {
  const router = useRouter()
  const locale = useLocale()
  const t = useTranslations("Procurement.purchaseOrders.list")
  const tCol = useTranslations("Procurement.purchaseOrders.columns")
  const tAct = useTranslations("Procurement.purchaseOrders.actions")
  const tPoStatus = useTranslations("Procurement.poStatus")
  const tShared = useTranslations("Procurement.shared")

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  })
  const [sorting, setSorting] = useState<SortingState>([
    { id: "order_date", desc: true },
  ])
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string[]>([])

  const statusQueryParam =
    statusFilter.length === 1 ? statusFilter[0] : undefined

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
    status: statusQueryParam,
  })

  const confirmMutation = useConfirmPurchaseOrder()
  const cancelMutation = useCancelPurchaseOrder()

  const STATUS_FILTER_OPTIONS: FacetedFilterOption[] = useMemo(
    () =>
      [...PO_STATUS_VALUES].map((v) => ({
        label: tPoStatus(v),
        value: v,
      })),
    [tPoStatus],
  )

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
          toast.success(t("toastConfirmed", { orderNumber: po.order_number })),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ?? tShared("unknownError")
          toast.error(t("confirmFailed", { message }))
        },
      })
    },
    [confirmMutation, t, tShared],
  )

  const handleCancel = useCallback(
    (po: PurchaseOrder) => {
      if (!confirm(t("cancelConfirm", { orderNumber: po.order_number }))) return
      cancelMutation.mutate(po.id, {
        onSuccess: () =>
          toast.success(t("toastCancelled", { orderNumber: po.order_number })),
        onError: (error) => {
          const message =
            (error as { message?: string }).message ?? tShared("unknownError")
          toast.error(t("cancelFailed", { message }))
        },
      })
    },
    [cancelMutation, t, tShared],
  )

  const columns = useMemo(
    () =>
      getPurchaseOrderColumns(
        {
          onView: handleView,
          onConfirm: handleConfirm,
          onCancel: handleCancel,
        },
        {
          tColumns: (key) => tCol(key),
          emDash: tShared("emDash"),
          viewLabel: tAct("view"),
          confirmLabel: tAct("confirm"),
          cancelLabel: tAct("cancel"),
          locale,
        },
      ),
    [handleView, handleConfirm, handleCancel, tCol, tShared, tAct, locale],
  )

  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  const statusFilterColumn = useMemo(
    () =>
      ({
        id: "status",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => statusFilter,
        setFilterValue: (val: unknown) => {
          setStatusFilter((val as string[] | undefined) ?? [])
          setPagination((p) => ({ ...p, pageIndex: 0 }))
        },
      }) as never,
    [statusFilter],
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title")}
        description={t("description")}
        actions={
          <Button onClick={() => router.push("/procurement/purchase-orders/new")}>
            <PlusIcon className="mr-2 size-4" />
            {t("newButton")}
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
            column={statusFilterColumn}
            title={t("statusFilter")}
            options={STATUS_FILTER_OPTIONS}
          />
        }
      />
    </div>
  )
}
