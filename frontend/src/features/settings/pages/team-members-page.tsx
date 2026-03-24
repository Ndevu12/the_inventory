"use client"

import * as React from "react"
import type { PaginationState } from "@tanstack/react-table"
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
import { useMembers, useUpdateMember, useRemoveMember } from "../hooks/use-members"
import { getMemberColumns } from "../components/member-columns"
import { MemberTable } from "../components/member-table"
import { InviteMemberDialog } from "../components/invite-member-dialog"
import { PendingInvitations } from "../components/pending-invitations"
import type { TenantMember, TenantRole } from "../types/settings.types"

export function TeamMembersPage() {
  const t = useTranslations("SettingsTenant")
  const tRoles = useTranslations("SettingsTenant.roles")
  const tCommon = useTranslations("Common.actions")

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  })
  const [search, setSearch] = React.useState("")
  const [memberToRemove, setMemberToRemove] =
    React.useState<TenantMember | null>(null)

  const { data, isLoading } = useMembers({
    page: pagination.pageIndex + 1,
    page_size: pagination.pageSize,
    search: search || undefined,
    ordering: "role",
  })

  const updateMutation = useUpdateMember()
  const removeMutation = useRemoveMember()

  const handleRoleChange = React.useCallback(
    (member: TenantMember, role: TenantRole) => {
      updateMutation.mutate(
        { id: member.id, payload: { role } },
        {
          onSuccess: () =>
            toast.success(
              t("members.toast.roleUpdated", {
                username: member.username,
                role: tRoles(role),
              }),
            ),
          onError: () => toast.error(t("members.toast.roleFailed")),
        },
      )
    },
    [updateMutation, t, tRoles],
  )

  const handleRemoveConfirm = React.useCallback(() => {
    if (!memberToRemove) return
    removeMutation.mutate(memberToRemove.id, {
      onSuccess: () => {
        toast.success(
          t("members.toast.removed", { username: memberToRemove.username }),
        )
        setMemberToRemove(null)
      },
      onError: () => toast.error(t("members.toast.removeFailed")),
    })
  }, [memberToRemove, removeMutation, t])

  const columns = React.useMemo(
    () =>
      getMemberColumns({
        onRoleChange: handleRoleChange,
        onRemove: setMemberToRemove,
        isUpdating: updateMutation.isPending,
        t,
      }),
    [handleRoleChange, updateMutation.isPending, t],
  )

  const members = data?.results ?? []
  const pageCount = data ? Math.ceil(data.count / pagination.pageSize) : 0

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title={t("members.page.title")}
          description={t("members.page.description")}
        />
        <InviteMemberDialog />
      </div>

      <PendingInvitations />

      <MemberTable
        columns={columns}
        data={members}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        searchValue={search}
        onSearchChange={setSearch}
        isLoading={isLoading}
      />

      <AlertDialog
        open={memberToRemove !== null}
        onOpenChange={(open) => {
          if (!open) setMemberToRemove(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("members.removeDialog.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("members.removeDialog.descriptionLead")}{" "}
              <strong>{memberToRemove?.username}</strong>{" "}
              {t("members.removeDialog.descriptionTrail")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleRemoveConfirm}
              disabled={removeMutation.isPending}
            >
              {removeMutation.isPending
                ? t("members.removing")
                : t("members.remove")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
