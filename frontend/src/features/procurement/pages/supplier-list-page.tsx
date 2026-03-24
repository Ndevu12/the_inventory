"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { useSuppliers, useDeleteSupplier } from "../hooks/use-suppliers"
import { getSupplierColumns } from "../components/supplier-columns"
import { SupplierTable } from "../components/suppliers/supplier-table"
import type { Supplier } from "../types/procurement.types"

export function SupplierListPage() {
  const router = useRouter()
  const t = useTranslations("Procurement.suppliers.list")
  const tCol = useTranslations("Procurement.suppliers.columns")
  const tPay = useTranslations("Procurement.paymentTerms")
  const tShared = useTranslations("Procurement.shared")
  const tInv = useTranslations("Inventory.shared")
  const tTable = useTranslations("Inventory.tableActions")

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  })
  const [search, setSearch] = React.useState("")

  const { data, isLoading } = useSuppliers({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    search: search || undefined,
    ordering: "name",
  })

  const deleteMutation = useDeleteSupplier()

  const handleEdit = React.useCallback(
    (supplier: Supplier) => {
      router.push(`/procurement/suppliers/${supplier.id}/edit`)
    },
    [router],
  )

  const handleDelete = React.useCallback(
    (supplier: Supplier) => {
      if (!confirm(t("deleteConfirm", { name: supplier.name }))) return
      deleteMutation.mutate(supplier.id, {
        onSuccess: () => toast.success(t("toastDeleted", { name: supplier.name })),
        onError: () => toast.error(t("toastDeleteFailed")),
      })
    },
    [deleteMutation, t],
  )

  const columns = React.useMemo(
    () =>
      getSupplierColumns(
        { onEdit: handleEdit, onDelete: handleDelete },
        {
          tColumns: (key, values) => tCol(key, values as Record<string, string | number>),
          tPaymentTerms: (key) => tPay(key),
          emDash: tShared("emDash"),
          activeLabel: tInv("active"),
          inactiveLabel: tInv("inactive"),
          editLabel: tTable("edit"),
          deleteLabel: tTable("delete"),
        },
      ),
    [
      handleEdit,
      handleDelete,
      tCol,
      tPay,
      tShared,
      tInv,
      tTable,
    ],
  )

  const suppliers = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("title")}
        description={t("description")}
        actions={
          <Button render={<Link href="/procurement/suppliers/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("newButton")}
          </Button>
        }
      />

      <SupplierTable
        columns={columns}
        data={suppliers}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={search}
        onSearchChange={setSearch}
        isLoading={isLoading}
      />
    </div>
  )
}
