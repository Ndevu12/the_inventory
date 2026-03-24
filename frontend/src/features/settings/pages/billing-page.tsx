"use client"

import * as React from "react"
import type { ColumnDef } from "@tanstack/react-table"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

import { PageHeader } from "@/components/layout/page-header"
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DataTable } from "@/components/data-table"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import {
  useBillingTenants,
  useUpdateBillingTenant,
  useSuspendBillingTenant,
  useReactivateBillingTenant,
} from "../hooks/use-billing"
import type { BillingTenant, SubscriptionPlan, SubscriptionStatus } from "../types/settings.types"
import {
  SUBSCRIPTION_PLAN_VALUES,
  SUBSCRIPTION_STATUS_VALUES,
} from "../helpers/settings-constants"
import { exportTenantData } from "../api/billing-api"
import { DownloadIcon, PencilIcon, PlayIcon, StopCircleIcon } from "lucide-react"

export function BillingPage() {
  const tb = useTranslations("SettingsPlatform.billing")
  const tPlans = useTranslations("SettingsTenant.plans")
  const tSubStatus = useTranslations("SettingsTenant.subscriptionStatus")
  const tCommon = useTranslations("Common.actions")

  const [tenantToEdit, setTenantToEdit] = React.useState<BillingTenant | null>(null)
  const [tenantToSuspend, setTenantToSuspend] = React.useState<BillingTenant | null>(null)
  const [tenantToReactivate, setTenantToReactivate] = React.useState<BillingTenant | null>(null)
  const [exportingId, setExportingId] = React.useState<number | null>(null)

  const { data: tenants = [], isLoading } = useBillingTenants()
  const updateMutation = useUpdateBillingTenant()
  const suspendMutation = useSuspendBillingTenant()
  const reactivateMutation = useReactivateBillingTenant()

  const handleSuspendConfirm = React.useCallback(() => {
    if (!tenantToSuspend) return
    suspendMutation.mutate(tenantToSuspend.id, {
      onSuccess: () => {
        toast.success(tb("toast.suspended", { name: tenantToSuspend.name }))
        setTenantToSuspend(null)
      },
      onError: () => toast.error(tb("toast.suspendFailed")),
    })
  }, [tenantToSuspend, suspendMutation, tb])

  const handleReactivateConfirm = React.useCallback(() => {
    if (!tenantToReactivate) return
    reactivateMutation.mutate(tenantToReactivate.id, {
      onSuccess: () => {
        toast.success(tb("toast.reactivated", { name: tenantToReactivate.name }))
        setTenantToReactivate(null)
      },
      onError: () => toast.error(tb("toast.reactivateFailed")),
    })
  }, [tenantToReactivate, reactivateMutation, tb])

  const handleExportTenant = React.useCallback(
    async (tenant: BillingTenant) => {
      setExportingId(tenant.id)
      try {
        await exportTenantData(tenant.id)
        toast.success(tb("toast.exportSuccess", { name: tenant.name }))
      } catch {
        toast.error(tb("toast.exportFailed"))
      } finally {
        setExportingId(null)
      }
    },
    [tb],
  )

  const columns: ColumnDef<BillingTenant>[] = React.useMemo(
    () => [
      {
        accessorKey: "name",
        header: tb("columns.tenant"),
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{row.original.name}</span>
            <span className="text-xs text-muted-foreground">{row.original.slug}</span>
          </div>
        ),
      },
      {
        accessorKey: "subscription_plan",
        header: tb("columns.plan"),
        cell: ({ row }) => (
          <Badge variant="outline">
            {tPlans(row.original.subscription_plan as SubscriptionPlan)}
          </Badge>
        ),
      },
      {
        accessorKey: "subscription_status",
        header: tb("columns.status"),
        cell: ({ row }) => (
          <Badge
            variant={
              row.original.subscription_status === "active"
                ? "default"
                : row.original.subscription_status === "suspended"
                  ? "destructive"
                  : "secondary"
            }
          >
            {tSubStatus(row.original.subscription_status as SubscriptionStatus)}
          </Badge>
        ),
      },
      {
        id: "active",
        header: tb("columns.active"),
        cell: ({ row }) => (
          <Badge variant={row.original.is_active ? "default" : "secondary"}>
            {row.original.is_active ? tb("yes") : tb("no")}
          </Badge>
        ),
      },
      {
        id: "usage",
        header: tb("columns.usage"),
        cell: ({ row }) => {
          const tenant = row.original
          const usersOver = tenant.user_count >= tenant.effective_max_users
          const productsOver = tenant.product_count >= tenant.effective_max_products
          return (
            <div className="flex flex-col gap-0.5 text-sm">
              <span className={usersOver ? "text-destructive" : ""}>
                {tb("usageUsers", {
                  current: tenant.user_count,
                  max: tenant.effective_max_users,
                })}
              </span>
              <span className={productsOver ? "text-destructive" : ""}>
                {tb("usageProducts", {
                  current: tenant.product_count,
                  max: tenant.effective_max_products,
                })}
              </span>
            </div>
          )
        },
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const tenant = row.original
          const isExporting = exportingId === tenant.id
          return (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => handleExportTenant(tenant)}
                disabled={isExporting}
                title={tb("ariaExport")}
              >
                <DownloadIcon className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setTenantToEdit(tenant)}
                title={tb("ariaChangePlan")}
              >
                <PencilIcon className="size-4" />
              </Button>
              {tenant.is_active ? (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-destructive"
                  onClick={() => setTenantToSuspend(tenant)}
                  title={tb("ariaSuspend")}
                >
                  <StopCircleIcon className="size-4" />
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-green-600"
                  onClick={() => setTenantToReactivate(tenant)}
                  title={tb("ariaReactivate")}
                >
                  <PlayIcon className="size-4" />
                </Button>
              )}
            </div>
          )
        },
        enableSorting: false,
        enableHiding: false,
      },
    ],
    [tb, tPlans, tSubStatus, handleExportTenant, exportingId],
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={tb("page.title")}
        description={tb("page.description")}
      />

      <DataTable
        columns={columns}
        data={tenants}
        searchValue=""
        onSearchChange={() => {}}
        searchPlaceholder={tb("searchPlaceholder")}
        isLoading={isLoading}
        emptyMessage={tb("emptyMessage")}
      />

      <AlertDialog
        open={tenantToSuspend !== null}
        onOpenChange={(open) => {
          if (!open) setTenantToSuspend(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tb("suspendDialog.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {tb("suspendDialog.descriptionLead")}{" "}
              <strong>{tenantToSuspend?.name}</strong>
              {tb("suspendDialog.descriptionTrail")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleSuspendConfirm}
              disabled={suspendMutation.isPending}
            >
              {suspendMutation.isPending ? tb("suspending") : tb("suspend")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={tenantToReactivate !== null}
        onOpenChange={(open) => {
          if (!open) setTenantToReactivate(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tb("reactivateDialog.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {tb("reactivateDialog.descriptionLead")}{" "}
              <strong>{tenantToReactivate?.name}</strong>
              {tb("reactivateDialog.descriptionTrail")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReactivateConfirm}
              disabled={reactivateMutation.isPending}
            >
              {reactivateMutation.isPending ? tb("reactivating") : tb("reactivate")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ChangePlanDialog
        tenant={tenantToEdit}
        onClose={() => setTenantToEdit(null)}
        onSuccess={() => {
          toast.success(tb("toast.subscriptionUpdated"))
          setTenantToEdit(null)
        }}
        updateMutation={updateMutation}
      />
    </div>
  )
}

function ChangePlanDialog({
  tenant,
  onClose,
  onSuccess,
  updateMutation,
}: {
  tenant: BillingTenant | null
  onClose: () => void
  onSuccess: () => void
  updateMutation: ReturnType<typeof useUpdateBillingTenant>
}) {
  const tcp = useTranslations("SettingsPlatform.billing.changePlan")
  const tPlans = useTranslations("SettingsTenant.plans")
  const tSubStatus = useTranslations("SettingsTenant.subscriptionStatus")
  const tCommon = useTranslations("Common.actions")

  const [plan, setPlan] = React.useState<SubscriptionPlan>("free")
  const [status, setStatus] = React.useState<SubscriptionStatus>("active")
  const [notes, setNotes] = React.useState("")

  React.useEffect(() => {
    if (tenant) {
      setPlan(tenant.subscription_plan as SubscriptionPlan)
      setStatus(tenant.subscription_status as SubscriptionStatus)
      setNotes(tenant.billing_notes ?? "")
    }
  }, [tenant])

  const tb = useTranslations("SettingsPlatform.billing")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!tenant) return
    updateMutation.mutate(
      { id: tenant.id, payload: { subscription_plan: plan, subscription_status: status, billing_notes: notes || undefined } },
      {
        onSuccess,
        onError: () => toast.error(tb("toast.subscriptionUpdateFailed")),
      },
    )
  }

  if (!tenant) return null

  return (
    <Dialog open={!!tenant} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{tcp("title", { name: tenant.name })}</DialogTitle>
          <DialogDescription>{tcp("description")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>{tcp("plan")}</Label>
            <Select value={plan} onValueChange={(v) => setPlan(v as SubscriptionPlan)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SUBSCRIPTION_PLAN_VALUES.map((p) => (
                  <SelectItem key={p} value={p}>
                    {tPlans(p)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>{tcp("status")}</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as SubscriptionStatus)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SUBSCRIPTION_STATUS_VALUES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {tSubStatus(s)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>{tcp("billingNotes")}</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={tcp("billingNotesPlaceholder")}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? tcp("saving") : tCommon("save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
