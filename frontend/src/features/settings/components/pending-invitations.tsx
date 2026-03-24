"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { XCircle, Clock, Mail } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
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
import { ROLE_COLOR_MAP } from "../helpers/settings-constants"
import { useInvitations, useCancelInvitation } from "../hooks/use-invitations"
import type { Invitation, TenantRole } from "../types/settings.types"
import { cn } from "@/lib/utils"

export function PendingInvitations() {
  const t = useTranslations("SettingsTenant.pendingInvitations")
  const tRoles = useTranslations("SettingsTenant.roles")
  const { data: invitations, isLoading } = useInvitations()
  const cancelMutation = useCancelInvitation()
  const [toCancel, setToCancel] = React.useState<Invitation | null>(null)

  const pending = React.useMemo(
    () => (invitations ?? []).filter((i) => i.status === "pending"),
    [invitations],
  )

  function handleCancelConfirm() {
    if (!toCancel) return
    cancelMutation.mutate(toCancel.id, {
      onSuccess: () => {
        toast.success(t("toastCancelled", { email: toCancel.email }))
        setToCancel(null)
      },
      onError: () => toast.error(t("toastCancelFailed")),
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (pending.length === 0) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Mail className="size-4" />
        {t("heading")} {t("headingCount", { count: pending.length })}
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("columns.email")}</TableHead>
              <TableHead>{t("columns.role")}</TableHead>
              <TableHead>{t("columns.status")}</TableHead>
              <TableHead>{t("columns.expires")}</TableHead>
              <TableHead className="w-[80px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {pending.map((inv) => {
              const roleColors = ROLE_COLOR_MAP[inv.role as TenantRole]
              const statusLabel = t(
                `invitationStatus.${inv.status}` as
                  | "invitationStatus.pending"
                  | "invitationStatus.accepted"
                  | "invitationStatus.cancelled"
                  | "invitationStatus.expired",
              )
              return (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">{inv.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn(
                        "border-transparent font-medium",
                        roleColors?.bg,
                        roleColors?.text,
                      )}
                    >
                      {tRoles(inv.role as TenantRole)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      <Clock className="mr-1 size-3" />
                      {statusLabel}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(inv.expires_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-8 text-muted-foreground hover:text-destructive"
                      onClick={() => setToCancel(inv)}
                    >
                      <XCircle className="size-4" />
                      <span className="sr-only">{t("srCancelInvitation")}</span>
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      <AlertDialog
        open={toCancel !== null}
        onOpenChange={(open) => {
          if (!open) setToCancel(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("cancelDialog.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("cancelDialog.descriptionLead")}{" "}
              <strong>{toCancel?.email}</strong>
              {t("cancelDialog.descriptionTrail")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("keep")}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleCancelConfirm}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? t("cancelling") : t("cancelInvitation")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
