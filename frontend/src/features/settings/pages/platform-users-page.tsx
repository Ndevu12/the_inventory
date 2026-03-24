"use client"

import * as React from "react"
import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

import { useAuth } from "@/features/auth/context/auth-context"
import { useImpersonate } from "@/features/auth/hooks/use-auth"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  usePlatformUsers,
  useCreatePlatformUser,
  usePlatformTenants,
  useRemovePlatformUser,
  useResetPlatformUserPassword,
} from "../hooks/use-platform-users"
import type { PlatformUser } from "../types/settings.types"
import { TENANT_ROLE_VALUES } from "../helpers/settings-constants"
import type { TenantRole } from "../types/settings.types"
import { PlusIcon, KeyIcon, TrashIcon, UserCogIcon } from "lucide-react"

function fullName(user: PlatformUser): string {
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ")
  return name || user.username
}

export function PlatformUsersPage() {
  const tu = useTranslations("SettingsPlatform.users")
  const tRoles = useTranslations("SettingsTenant.roles")
  const tCommon = useTranslations("Common.actions")

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 25,
  })
  const [search, setSearch] = React.useState("")
  const [userToSuspend, setUserToSuspend] = React.useState<PlatformUser | null>(null)
  const [passwordUserId, setPasswordUserId] = React.useState<number | null>(null)
  const [newPassword, setNewPassword] = React.useState("")
  const [showCreate, setShowCreate] = React.useState(false)

  const { data, isLoading } = usePlatformUsers({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    search: search || undefined,
    ordering: "-date_joined",
  })

  const removeMutation = useRemovePlatformUser()
  const resetPasswordMutation = useResetPlatformUserPassword()
  const impersonateMutation = useImpersonate()
  const { user: currentUser } = useAuth()
  const canImpersonate = currentUser?.is_superuser === true

  const handleSuspendConfirm = React.useCallback(() => {
    if (!userToSuspend) return
    removeMutation.mutate(userToSuspend.id, {
      onSuccess: () => {
        toast.success(tu("toast.userSuspended", { username: userToSuspend.username }))
        setUserToSuspend(null)
      },
      onError: () => toast.error(tu("toast.suspendFailed")),
    })
  }, [userToSuspend, removeMutation, tu])

  const handleResetPassword = React.useCallback(() => {
    if (!passwordUserId || !newPassword || newPassword.length < 8) return
    resetPasswordMutation.mutate(
      { id: passwordUserId, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success(tu("toast.passwordReset"))
          setPasswordUserId(null)
          setNewPassword("")
        },
        onError: () => toast.error(tu("toast.passwordResetFailed")),
      },
    )
  }, [passwordUserId, newPassword, resetPasswordMutation, tu])

  const columns: ColumnDef<PlatformUser>[] = React.useMemo(
    () => [
      {
        accessorKey: "username",
        header: tu("columns.user"),
        cell: ({ row }) => {
          const user = row.original
          return (
            <div className="flex flex-col">
              <span className="font-medium">{fullName(user)}</span>
              <span className="text-xs text-muted-foreground">@{user.username}</span>
            </div>
          )
        },
      },
      {
        accessorKey: "email",
        header: tu("columns.email"),
        cell: ({ row }) => (
          <span className="text-muted-foreground">
            {row.getValue("email") || "—"}
          </span>
        ),
      },
      {
        accessorKey: "is_active",
        header: tu("columns.status"),
        cell: ({ row }) => {
          const active = row.getValue<boolean>("is_active")
          return (
            <Badge variant={active ? "default" : "secondary"}>
              {active
                ? tu("userStatus.active")
                : tu("userStatus.suspended")}
            </Badge>
          )
        },
      },
      {
        accessorKey: "tenants_display",
        header: tu("columns.tenants"),
        cell: ({ row }) => {
          const tenants = row.original.tenants_display
          if (!tenants?.length) return <span className="text-muted-foreground">—</span>
          return (
            <div className="flex flex-wrap gap-1">
              {tenants.slice(0, 3).map((tenant) => (
                <Badge key={tenant.id} variant="outline" className="text-xs">
                  {tenant.name} ({tRoles(tenant.role as TenantRole)})
                </Badge>
              ))}
              {tenants.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  {tu("moreTenants", { count: tenants.length - 3 })}
                </Badge>
              )}
            </div>
          )
        },
        enableSorting: false,
      },
      {
        accessorKey: "date_joined",
        header: tu("columns.joined"),
        cell: ({ row }) => {
          const date = new Date(row.getValue<string>("date_joined"))
          return date.toLocaleDateString()
        },
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const user = row.original
          if (!user.is_active) return null
          const isCurrentUser = currentUser?.id === user.id
          return (
            <div className="flex items-center gap-1">
              {canImpersonate && !isCurrentUser && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={() =>
                    impersonateMutation.mutate(user.id, {
                      onSuccess: () =>
                        toast.success(tu("toast.impersonating", { username: user.username })),
                      onError: () => toast.error(tu("toast.impersonateFailed")),
                    })
                  }
                  disabled={impersonateMutation.isPending}
                  title={tu("ariaImpersonate")}
                >
                  <UserCogIcon className="size-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => {
                  setPasswordUserId(user.id)
                  setNewPassword("")
                }}
                title={tu("ariaResetPassword")}
              >
                <KeyIcon className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                onClick={() => setUserToSuspend(user)}
                title={tu("ariaSuspendUser")}
              >
                <TrashIcon className="size-4" />
              </Button>
            </div>
          )
        },
        enableSorting: false,
        enableHiding: false,
      },
    ],
    [tu, tRoles, canImpersonate, currentUser?.id, impersonateMutation],
  )

  const users = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title={tu("page.title")}
          description={tu("page.description")}
        />
        <Button onClick={() => setShowCreate(true)}>
          <PlusIcon className="mr-2 size-4" />
          {tu("createUser")}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={users}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder={tu("searchPlaceholder")}
        isLoading={isLoading}
        emptyMessage={tu("emptyMessage")}
      />

      <AlertDialog
        open={userToSuspend !== null}
        onOpenChange={(open) => {
          if (!open) setUserToSuspend(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tu("suspendDialog.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {tu("suspendDialog.descriptionLead")}{" "}
              <strong>{userToSuspend?.username}</strong>
              {tu("suspendDialog.descriptionTrail")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleSuspendConfirm}
              disabled={removeMutation.isPending}
            >
              {removeMutation.isPending ? tu("suspending") : tu("suspend")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog
        open={passwordUserId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPasswordUserId(null)
            setNewPassword("")
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{tu("resetPassword.title")}</DialogTitle>
            <DialogDescription>{tu("resetPassword.description")}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="new-password">{tu("resetPassword.newPassword")}</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={tu("resetPassword.placeholder")}
                minLength={8}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setPasswordUserId(null)
                setNewPassword("")
              }}
            >
              {tCommon("cancel")}
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={
                !newPassword ||
                newPassword.length < 8 ||
                resetPasswordMutation.isPending
              }
            >
              {resetPasswordMutation.isPending
                ? tu("resetPassword.resetting")
                : tu("resetPassword.reset")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <CreateUserDialog open={showCreate} onOpenChange={setShowCreate} />
    </div>
  )
}

function CreateUserDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const tc = useTranslations("SettingsPlatform.users.createDialog")
  const tRoles = useTranslations("SettingsTenant.roles")
  const tCommon = useTranslations("Common.actions")

  const [username, setUsername] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [tenantIds, setTenantIds] = React.useState<number[]>([])
  const [defaultRole, setDefaultRole] = React.useState<string>("viewer")

  const createMutation = useCreatePlatformUser()
  const { data: tenants = [] } = usePlatformTenants()
  const tu = useTranslations("SettingsPlatform.users")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(
      {
        username,
        email,
        password,
        tenant_ids: tenantIds.length ? tenantIds : undefined,
        default_role: defaultRole as "owner" | "admin" | "manager" | "viewer",
      },
      {
        onSuccess: () => {
          toast.success(tu("toast.userCreated", { username }))
          onOpenChange(false)
          setUsername("")
          setEmail("")
          setPassword("")
          setTenantIds([])
        },
        onError: (err: { message?: string }) =>
          toast.error(err?.message ?? tu("toast.createFailed")),
      },
    )
  }

  const handleTenantToggle = (id: number) => {
    setTenantIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{tc("title")}</DialogTitle>
          <DialogDescription>{tc("description")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="username">{tc("username")}</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder={tc("placeholderUsername")}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">{tc("email")}</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder={tc("placeholderEmail")}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">{tc("password")}</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder={tc("placeholderPassword")}
            />
          </div>
          <div className="grid gap-2">
            <Label>{tc("defaultRole")}</Label>
            <Select value={defaultRole} onValueChange={(val) => val && setDefaultRole(val)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TENANT_ROLE_VALUES.map((r) => (
                  <SelectItem key={r} value={r}>
                    {tRoles(r)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {tenants.length > 0 && (
            <div className="grid gap-2">
              <Label>{tc("assignTenants")}</Label>
              <div className="flex flex-wrap gap-2">
                {tenants.map((tenant) => (
                  <Button
                    key={tenant.id}
                    type="button"
                    variant={tenantIds.includes(tenant.id) ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleTenantToggle(tenant.id)}
                  >
                    {tenant.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? tc("creating") : tc("create")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
