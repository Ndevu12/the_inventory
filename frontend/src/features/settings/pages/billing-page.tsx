"use client"

import * as React from "react"
import type { ColumnDef } from "@tanstack/react-table"
import { toast } from "sonner"

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
  SUBSCRIPTION_PLAN_MAP,
  SUBSCRIPTION_STATUS_MAP,
} from "../helpers/settings-constants"
import { exportTenantData } from "../api/billing-api"
import { DownloadIcon, PencilIcon, PlayIcon, StopCircleIcon } from "lucide-react"

export function BillingPage() {
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
        toast.success(`${tenantToSuspend.name} has been suspended`)
        setTenantToSuspend(null)
      },
      onError: () => toast.error("Failed to suspend tenant"),
    })
  }, [tenantToSuspend, suspendMutation])

  const handleReactivateConfirm = React.useCallback(() => {
    if (!tenantToReactivate) return
    reactivateMutation.mutate(tenantToReactivate.id, {
      onSuccess: () => {
        toast.success(`${tenantToReactivate.name} has been reactivated`)
        setTenantToReactivate(null)
      },
      onError: () => toast.error("Failed to reactivate tenant"),
    })
  }, [tenantToReactivate, reactivateMutation])

  const handleExportTenant = React.useCallback(
    async (tenant: BillingTenant) => {
      setExportingId(tenant.id)
      try {
        await exportTenantData(tenant.id)
        toast.success(`Export for ${tenant.name} downloaded`)
      } catch {
        toast.error("Failed to export tenant data")
      } finally {
        setExportingId(null)
      }
    },
    [],
  )

  const columns: ColumnDef<BillingTenant>[] = React.useMemo(
    () => [
      {
        accessorKey: "name",
        header: "Tenant",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{row.original.name}</span>
            <span className="text-xs text-muted-foreground">{row.original.slug}</span>
          </div>
        ),
      },
      {
        accessorKey: "subscription_plan",
        header: "Plan",
        cell: ({ row }) => (
          <Badge variant="outline">
            {SUBSCRIPTION_PLAN_MAP[row.original.subscription_plan as SubscriptionPlan]}
          </Badge>
        ),
      },
      {
        accessorKey: "subscription_status",
        header: "Status",
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
            {SUBSCRIPTION_STATUS_MAP[row.original.subscription_status as SubscriptionStatus]}
          </Badge>
        ),
      },
      {
        id: "active",
        header: "Active",
        cell: ({ row }) => (
          <Badge variant={row.original.is_active ? "default" : "secondary"}>
            {row.original.is_active ? "Yes" : "No"}
          </Badge>
        ),
      },
      {
        id: "usage",
        header: "Usage",
        cell: ({ row }) => {
          const t = row.original
          const usersOver = t.user_count >= t.effective_max_users
          const productsOver = t.product_count >= t.effective_max_products
          return (
            <div className="flex flex-col gap-0.5 text-sm">
              <span className={usersOver ? "text-destructive" : ""}>
                {t.user_count}/{t.effective_max_users} users
              </span>
              <span className={productsOver ? "text-destructive" : ""}>
                {t.product_count}/{t.effective_max_products} products
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
                title="Export tenant data"
              >
                <DownloadIcon className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setTenantToEdit(tenant)}
                title="Change plan"
              >
                <PencilIcon className="size-4" />
              </Button>
              {tenant.is_active ? (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-destructive"
                  onClick={() => setTenantToSuspend(tenant)}
                  title="Suspend"
                >
                  <StopCircleIcon className="size-4" />
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-green-600"
                  onClick={() => setTenantToReactivate(tenant)}
                  title="Reactivate"
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
    []
  )

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Billing & Subscriptions"
        description="Manage tenant plans, usage, and billing (superuser only)"
      />

      <DataTable
        columns={columns}
        data={tenants}
        searchValue=""
        onSearchChange={() => {}}
        searchPlaceholder="Search tenants..."
        isLoading={isLoading}
        emptyMessage="No tenants found."
      />

      <AlertDialog
        open={tenantToSuspend !== null}
        onOpenChange={(open) => {
          if (!open) setTenantToSuspend(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Suspend tenant</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to suspend <strong>{tenantToSuspend?.name}</strong>? The tenant
              will not be able to log in or access data until reactivated.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleSuspendConfirm}
              disabled={suspendMutation.isPending}
            >
              {suspendMutation.isPending ? "Suspending…" : "Suspend"}
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
            <AlertDialogTitle>Reactivate tenant</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to reactivate <strong>{tenantToReactivate?.name}</strong>? The
              tenant will be able to log in and access data again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReactivateConfirm}
              disabled={reactivateMutation.isPending}
            >
              {reactivateMutation.isPending ? "Reactivating…" : "Reactivate"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ChangePlanDialog
        tenant={tenantToEdit}
        onClose={() => setTenantToEdit(null)}
        onSuccess={() => {
          toast.success("Subscription updated")
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!tenant) return
    updateMutation.mutate(
      { id: tenant.id, payload: { subscription_plan: plan, subscription_status: status, billing_notes: notes || undefined } },
      { onSuccess, onError: () => toast.error("Failed to update subscription") }
    )
  }

  if (!tenant) return null

  return (
    <Dialog open={!!tenant} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Change plan — {tenant.name}</DialogTitle>
          <DialogDescription>
            Update subscription plan, status, or billing notes.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Plan</Label>
            <Select value={plan} onValueChange={(v) => setPlan(v as SubscriptionPlan)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="free">Free</SelectItem>
                <SelectItem value="starter">Starter</SelectItem>
                <SelectItem value="professional">Professional</SelectItem>
                <SelectItem value="enterprise">Enterprise</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as SubscriptionStatus)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="trial">Trial</SelectItem>
                <SelectItem value="past_due">Past Due</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>Billing notes (optional)</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Payment issues, custom arrangements, etc."
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
