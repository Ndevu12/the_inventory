"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { useTranslations } from "next-intl"
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
import { useCustomers, useDeleteCustomer } from "../hooks/use-customers"
import { getCustomerColumns } from "../components/customer-columns"
import { CustomerTable } from "../components/customers/customer-table"
import type { Customer } from "../types/sales.types"

export function CustomerListPage() {
  const router = useRouter()
  const t = useTranslations("Sales.customers.list")
  const tCol = useTranslations("Sales.customers.columns")
  const tCust = useTranslations("Sales.customerStatus")
  const tShared = useTranslations("Sales.shared")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  })
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "name", desc: false },
  ])
  const [search, setSearch] = React.useState("")

  const ordering = sorting.length
    ? `${sorting[0].desc ? "-" : ""}${sorting[0].id}`
    : "name"

  const { data, isLoading } = useCustomers({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    search: search || undefined,
    ordering,
  })

  const deleteMutation = useDeleteCustomer()

  const [customerToDelete, setCustomerToDelete] =
    React.useState<Customer | null>(null)

  const handleEdit = React.useCallback(
    (customer: Customer) => {
      router.push(`/sales/customers/${customer.id}/edit`)
    },
    [router],
  )

  const handleDelete = React.useCallback((customer: Customer) => {
    setCustomerToDelete(customer)
  }, [])

  const confirmDeleteCustomer = React.useCallback(() => {
    if (!customerToDelete) return
    deleteMutation.mutate(customerToDelete.id, {
      onSuccess: () => {
        toast.success(
          t("toastDeleted", { name: customerToDelete.name }),
        )
        setCustomerToDelete(null)
      },
      onError: () => toast.error(t("toastDeleteFailed")),
    })
  }, [customerToDelete, deleteMutation, t])

  const columnLabels = React.useMemo(
    () => ({
      tColumns: (key: string) => tCol(key),
      emDash: tShared("emDash"),
      activeLabel: tCust("active"),
      inactiveLabel: tCust("inactive"),
    }),
    [tCol, tShared, tCust],
  )

  const columns = React.useMemo(
    () =>
      getCustomerColumns(
        { onEdit: handleEdit, onDelete: handleDelete },
        columnLabels,
      ),
    [handleEdit, handleDelete, columnLabels],
  )

  const customers = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("title")}
        description={t("description")}
        actions={
          <Button render={<Link href="/sales/customers/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("newButton")}
          </Button>
        }
      />

      <CustomerTable
        columns={columns}
        data={customers}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        sorting={sorting}
        onSortingChange={setSorting}
        searchValue={search}
        onSearchChange={setSearch}
        isLoading={isLoading}
      />

      <AlertDialog
        open={customerToDelete != null}
        onOpenChange={(open) => {
          if (!open) setCustomerToDelete(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tCommon("delete")}</AlertDialogTitle>
            <AlertDialogDescription>
              {customerToDelete
                ? t("deleteConfirm", { name: customerToDelete.name })
                : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>
              {tCommon("cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={confirmDeleteCustomer}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending
                ? tCommonStates("loading")
                : tCommon("delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
