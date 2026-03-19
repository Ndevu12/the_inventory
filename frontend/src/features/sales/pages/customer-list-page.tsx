"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import type { PaginationState, SortingState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { useCustomers, useDeleteCustomer } from "../hooks/use-customers"
import { getCustomerColumns } from "../components/customer-columns"
import { CustomerTable } from "../components/customers/customer-table"
import type { Customer } from "../types/sales.types"

export function CustomerListPage() {
  const router = useRouter()

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

  const handleEdit = React.useCallback(
    (customer: Customer) => {
      router.push(`/sales/customers/${customer.id}/edit`)
    },
    [router]
  )

  const handleDelete = React.useCallback(
    (customer: Customer) => {
      if (!confirm(`Delete customer "${customer.name}"?`)) return
      deleteMutation.mutate(customer.id, {
        onSuccess: () => toast.success(`Customer "${customer.name}" deleted`),
        onError: () => toast.error("Failed to delete customer"),
      })
    },
    [deleteMutation]
  )

  const columns = React.useMemo(
    () => getCustomerColumns({ onEdit: handleEdit, onDelete: handleDelete }),
    [handleEdit, handleDelete]
  )

  const customers = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Customers"
        description="Manage your customer directory"
        actions={
          <Button render={<Link href="/sales/customers/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            New Customer
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
    </div>
  )
}
