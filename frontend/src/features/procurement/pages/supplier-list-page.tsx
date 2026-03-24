"use client"

import * as React from "react"
import { Link } from "@/i18n/navigation"
import { useRouter } from "@/i18n/navigation"
import type { PaginationState } from "@tanstack/react-table"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { useSuppliers, useDeleteSupplier } from "../hooks/use-suppliers"
import { getSupplierColumns } from "../components/supplier-columns"
import { SupplierTable } from "../components/suppliers/supplier-table"
import type { Supplier } from "../types/procurement.types"

export function SupplierListPage() {
  const router = useRouter()

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
      router.push(`/suppliers/${supplier.id}/edit`)
    },
    [router]
  )

  const handleDelete = React.useCallback(
    (supplier: Supplier) => {
      if (!confirm(`Delete supplier "${supplier.name}"?`)) return
      deleteMutation.mutate(supplier.id, {
        onSuccess: () => toast.success(`Supplier "${supplier.name}" deleted`),
        onError: () => toast.error("Failed to delete supplier"),
      })
    },
    [deleteMutation]
  )

  const columns = React.useMemo(
    () => getSupplierColumns({ onEdit: handleEdit, onDelete: handleDelete }),
    [handleEdit, handleDelete]
  )

  const suppliers = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Suppliers"
        description="Manage your supplier directory"
        actions={
          <Button render={<Link href="/suppliers/new" />}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            New Supplier
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
