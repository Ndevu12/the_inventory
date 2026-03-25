"use client"

import { useDeferredValue, useState } from "react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { Building2Icon, MoreHorizontalIcon, PlusIcon, SearchIcon } from "lucide-react"
import { Link } from "@/i18n/navigation"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
import {
  useWarehousesList,
  useDeleteWarehouse,
} from "../hooks/use-warehouses"
import { WarehouseFormDialog } from "../components/warehouses/warehouse-form-dialog"
import { formatDate } from "../helpers/inventory-formatters"
import type { Warehouse } from "../types/warehouse.types"
import type { ApiError } from "@/types"

export function WarehouseListPage() {
  const t = useTranslations("Inventory")
  const tShared = useTranslations("Inventory.shared")
  const tTable = useTranslations("Inventory.tableActions")
  const [search, setSearch] = useState("")
  const deferredSearch = useDeferredValue(search)
  const { data: rows = [], isLoading } = useWarehousesList(deferredSearch)
  const deleteMutation = useDeleteWarehouse()
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Warehouse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Warehouse | null>(null)

  function openCreate() {
    setEditTarget(null)
    setFormOpen(true)
  }

  function openEdit(w: Warehouse) {
    setEditTarget(w)
    setFormOpen(true)
  }

  function closeForm(open: boolean) {
    setFormOpen(open)
    if (!open) setEditTarget(null)
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deleteMutation.mutateAsync(deleteTarget.id)
      toast.success(
        t("warehouses.toastDeleted", { name: deleteTarget.name }),
      )
      setDeleteTarget(null)
    } catch (err) {
      const apiErr = err as ApiError
      toast.error(apiErr?.message || t("warehouses.toastDeleteFailed"))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("warehouses.title")}
        description={t("warehouses.description")}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" render={<Link href="/stock/locations" />}>
              {t("warehouses.goToStockLocations")}
            </Button>
            <Button onClick={openCreate}>
              <PlusIcon className="size-4" data-icon="inline-start" />
              {t("warehouses.addWarehouse")}
            </Button>
          </div>
        }
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative max-w-sm flex-1">
          <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t("warehouses.searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <Building2Icon className="mb-4 size-12 text-muted-foreground/50" />
          <h3 className="font-medium">{t("warehouses.emptyTitle")}</h3>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            {t("warehouses.emptyDescription")}
          </p>
          <Button className="mt-4" onClick={openCreate}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            {t("warehouses.addWarehouse")}
          </Button>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("warehouses.columns.name")}</TableHead>
                <TableHead>{t("warehouses.columns.status")}</TableHead>
                <TableHead className="hidden md:table-cell">
                  {t("warehouses.columns.timezone")}
                </TableHead>
                <TableHead className="hidden lg:table-cell">
                  {t("warehouses.columns.updated")}
                </TableHead>
                <TableHead className="w-[52px] text-right">
                  <span className="sr-only">{tTable("openMenu")}</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((w) => (
                <TableRow key={w.id}>
                  <TableCell className="font-medium">{w.name}</TableCell>
                  <TableCell>
                    <Badge variant={w.is_active ? "default" : "secondary"}>
                      {w.is_active ? tShared("active") : tShared("inactive")}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">
                    {w.timezone_name}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">
                    {formatDate(w.updated_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button
                            variant="ghost"
                            size="icon"
                            className="flex size-8 data-[state=open]:bg-muted"
                          />
                        }
                      >
                        <MoreHorizontalIcon className="size-4" />
                        <span className="sr-only">{tTable("openMenu")}</span>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEdit(w)}>
                          {tTable("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setDeleteTarget(w)}
                        >
                          {tTable("delete")}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <WarehouseFormDialog
        open={formOpen}
        onOpenChange={closeForm}
        warehouse={editTarget}
      />

      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("warehouses.deleteTitle")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("warehouses.deleteDescription", {
                name: deleteTarget?.name ?? "",
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("warehouses.deleteCancel")}</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={confirmDelete}
            >
              {t("warehouses.deleteConfirm")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
