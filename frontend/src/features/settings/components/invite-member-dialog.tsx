"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { UserPlus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TENANT_ROLE_VALUES } from "../helpers/settings-constants"
import { useCreateInvitation } from "../hooks/use-invitations"
import type { TenantRole } from "../types/settings.types"

export function InviteMemberDialog() {
  const t = useTranslations("SettingsTenant.invite")
  const tRoles = useTranslations("SettingsTenant.roles")
  const tCommon = useTranslations("Common.actions")
  const [open, setOpen] = React.useState(false)
  const [email, setEmail] = React.useState("")
  const [role, setRole] = React.useState<TenantRole>("viewer")

  const createInvitation = useCreateInvitation()

  const assignableRoles = TENANT_ROLE_VALUES.filter((r) => r !== "owner")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return

    createInvitation.mutate(
      { email: email.trim().toLowerCase(), role },
      {
        onSuccess: () => {
          toast.success(t("toastSent", { email: email.trim() }))
          setEmail("")
          setRole("viewer")
          setOpen(false)
        },
        onError: (error) => {
          const msg =
            (error as { message?: string }).message ?? t("toastFailed")
          toast.error(msg)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" />}>
        <UserPlus className="mr-2 size-4" />
        {t("trigger")}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{t("title")}</DialogTitle>
            <DialogDescription>{t("description")}</DialogDescription>
          </DialogHeader>

          <div className="mt-4 grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="invite-email">{t("email")}</Label>
              <Input
                id="invite-email"
                type="email"
                placeholder={t("placeholderEmail")}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="invite-role">{t("role")}</Label>
              <Select
                value={role}
                onValueChange={(v) => setRole(v as TenantRole)}
              >
                <SelectTrigger id="invite-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {assignableRoles.map((r) => (
                    <SelectItem key={r} value={r}>
                      {tRoles(r)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={createInvitation.isPending}>
              {createInvitation.isPending ? t("sending") : t("sendInvitation")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
