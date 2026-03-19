"use client"

import * as React from "react"
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
import { ROLE_MAP, ROLE_COLOR_MAP } from "../helpers/settings-constants"
import { useInvitations, useCancelInvitation } from "../hooks/use-invitations"
import type { Invitation, TenantRole } from "../types/settings.types"
import { cn } from "@/lib/utils"

const STATUS_BADGE: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
  pending: { variant: "outline", label: "Pending" },
  accepted: { variant: "default", label: "Accepted" },
  cancelled: { variant: "secondary", label: "Cancelled" },
  expired: { variant: "destructive", label: "Expired" },
}

export function PendingInvitations() {
  const { data: invitations, isLoading } = useInvitations()
  const cancelMutation = useCancelInvitation()
  const [toCancel, setToCancel] = React.useState<Invitation | null>(null)

  const pending = React.useMemo(
    () => (invitations ?? []).filter((i) => i.status === "pending"),
    [invitations]
  )

  function handleCancelConfirm() {
    if (!toCancel) return
    cancelMutation.mutate(toCancel.id, {
      onSuccess: () => {
        toast.success(`Invitation to ${toCancel.email} cancelled`)
        setToCancel(null)
      },
      onError: () => toast.error("Failed to cancel invitation"),
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
        Pending Invitations ({pending.length})
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead className="w-[80px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {pending.map((inv) => {
              const roleColors = ROLE_COLOR_MAP[inv.role as TenantRole]
              const statusInfo = STATUS_BADGE[inv.status] ?? STATUS_BADGE.pending
              return (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">{inv.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn(
                        "border-transparent font-medium",
                        roleColors?.bg,
                        roleColors?.text
                      )}
                    >
                      {ROLE_MAP[inv.role as TenantRole] ?? inv.role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusInfo.variant}>
                      <Clock className="mr-1 size-3" />
                      {statusInfo.label}
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
                      <span className="sr-only">Cancel invitation</span>
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
        onOpenChange={(open) => { if (!open) setToCancel(null) }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel invitation</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel the invitation to{" "}
              <strong>{toCancel?.email}</strong>? The invitation link will no
              longer work.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleCancelConfirm}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? "Cancelling…" : "Cancel Invitation"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
