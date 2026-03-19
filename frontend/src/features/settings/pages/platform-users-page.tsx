"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import type { ColumnDef, PaginationState } from "@tanstack/react-table"
import { toast } from "sonner"

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
import { ROLE_MAP } from "../helpers/settings-constants"
import { PlusIcon, KeyIcon, TrashIcon, UserCogIcon } from "lucide-react"

function fullName(user: PlatformUser): string {
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ")
  return name || user.username
}

export function PlatformUsersPage() {
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
        toast.success(`${userToSuspend.username} has been suspended`)
        setUserToSuspend(null)
      },
      onError: () => toast.error("Failed to suspend user"),
    })
  }, [userToSuspend, removeMutation])

  const handleResetPassword = React.useCallback(() => {
    if (!passwordUserId || !newPassword || newPassword.length < 8) return
    resetPasswordMutation.mutate(
      { id: passwordUserId, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success("Password has been reset")
          setPasswordUserId(null)
          setNewPassword("")
        },
        onError: () => toast.error("Failed to reset password"),
      }
    )
  }, [passwordUserId, newPassword, resetPasswordMutation])

  const columns: ColumnDef<PlatformUser>[] = React.useMemo(
    () => [
      {
        accessorKey: "username",
        header: "User",
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
        header: "Email",
        cell: ({ row }) => (
          <span className="text-muted-foreground">
            {row.getValue("email") || "—"}
          </span>
        ),
      },
      {
        accessorKey: "is_active",
        header: "Status",
        cell: ({ row }) => {
          const active = row.getValue<boolean>("is_active")
          return (
            <Badge variant={active ? "default" : "secondary"}>
              {active ? "Active" : "Suspended"}
            </Badge>
          )
        },
      },
      {
        accessorKey: "tenants_display",
        header: "Tenants",
        cell: ({ row }) => {
          const tenants = row.original.tenants_display
          if (!tenants?.length) return <span className="text-muted-foreground">—</span>
          return (
            <div className="flex flex-wrap gap-1">
              {tenants.slice(0, 3).map((t) => (
                <Badge key={t.id} variant="outline" className="text-xs">
                  {t.name} ({ROLE_MAP[t.role as keyof typeof ROLE_MAP] ?? t.role})
                </Badge>
              ))}
              {tenants.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{tenants.length - 3}
                </Badge>
              )}
            </div>
          )
        },
        enableSorting: false,
      },
      {
        accessorKey: "date_joined",
        header: "Joined",
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
                        toast.success(`Impersonating ${user.username}`),
                      onError: () => toast.error("Failed to impersonate"),
                    })
                  }
                  disabled={impersonateMutation.isPending}
                  title="Impersonate"
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
                title="Reset password"
              >
                <KeyIcon className="size-4" />
              </Button>
              {canImpersonate && user.id !== currentUser?.id && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={() =>
                    impersonateMutation.mutate(user.id, {
                      onSuccess: () =>
                        toast.success(`Impersonating ${user.username}`),
                      onError: () => toast.error("Failed to impersonate"),
                    })
                  }
                  disabled={impersonateMutation.isPending}
                  title="Impersonate"
                >
                  <UserCogIcon className="size-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                onClick={() => setUserToSuspend(user)}
                title="Suspend user"
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
    [canImpersonate, currentUser?.id, impersonateMutation],
  )

  const users = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Platform Users"
          description="Manage all users across tenants (superuser only)"
        />
        <Button onClick={() => setShowCreate(true)}>
          <PlusIcon className="mr-2 size-4" />
          Create User
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
        searchPlaceholder="Search by email or username..."
        isLoading={isLoading}
        emptyMessage="No users found."
      />

      {/* Suspend confirmation */}
      <AlertDialog
        open={userToSuspend !== null}
        onOpenChange={(open) => {
          if (!open) setUserToSuspend(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Suspend user</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to suspend{" "}
              <strong>{userToSuspend?.username}</strong>? They will lose access
              to all tenants. This can be reversed by editing the user.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleSuspendConfirm}
              disabled={removeMutation.isPending}
            >
              {removeMutation.isPending ? "Suspending…" : "Suspend"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset password dialog */}
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
            <DialogTitle>Reset password</DialogTitle>
            <DialogDescription>
              Enter a new password for this user. Minimum 8 characters.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min 8 characters"
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
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={
                !newPassword ||
                newPassword.length < 8 ||
                resetPasswordMutation.isPending
              }
            >
              {resetPasswordMutation.isPending ? "Resetting…" : "Reset"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create user dialog - simplified for now, full form can be added */}
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
  const [username, setUsername] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [tenantIds, setTenantIds] = React.useState<number[]>([])
  const [defaultRole, setDefaultRole] = React.useState<string>("viewer")

  const createMutation = useCreatePlatformUser()
  const { data: tenants = [] } = usePlatformTenants()

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
          toast.success(`User ${username} created`)
          onOpenChange(false)
          setUsername("")
          setEmail("")
          setPassword("")
          setTenantIds([])
        },
        onError: (err: { message?: string }) =>
          toast.error(err?.message ?? "Failed to create user"),
      }
    )
  }

  const handleTenantToggle = (id: number) => {
    setTenantIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create user</DialogTitle>
          <DialogDescription>
            Create a new user and optionally assign them to tenants.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="jdoe"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="jane@example.com"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder="Min 8 characters"
            />
          </div>
          <div className="grid gap-2">
            <Label>Default role (for assigned tenants)</Label>
            <Select value={defaultRole} onValueChange={setDefaultRole}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="viewer">Viewer</SelectItem>
                <SelectItem value="manager">Manager</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="owner">Owner</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {tenants.length > 0 && (
            <div className="grid gap-2">
              <Label>Assign to tenants</Label>
              <div className="flex flex-wrap gap-2">
                {tenants.map((t) => (
                  <Button
                    key={t.id}
                    type="button"
                    variant={tenantIds.includes(t.id) ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleTenantToggle(t.id)}
                  >
                    {t.name}
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
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
