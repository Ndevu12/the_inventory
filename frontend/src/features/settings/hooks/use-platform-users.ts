"use client"

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { platformUsersApi, platformTenantsApi } from "../api/users-api"
import type {
  PlatformUserListParams,
  PlatformUserCreatePayload,
  PlatformUserUpdatePayload,
} from "../types/settings.types"

const USERS_KEY = ["platform-users"] as const
const TENANTS_KEY = ["platform-tenants"] as const

export function usePlatformUsers(params?: PlatformUserListParams) {
  return useQuery({
    queryKey: [...USERS_KEY, params],
    queryFn: () => platformUsersApi.list(params),
  })
}

export function usePlatformUser(id: number) {
  return useQuery({
    queryKey: [...USERS_KEY, id],
    queryFn: () => platformUsersApi.get(id),
    enabled: id > 0,
  })
}

export function usePlatformTenants() {
  return useQuery({
    queryKey: TENANTS_KEY,
    queryFn: () => platformTenantsApi.list(),
  })
}

export function useCreatePlatformUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: PlatformUserCreatePayload) =>
      platformUsersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USERS_KEY })
    },
  })
}

export function useUpdatePlatformUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: { id: number; payload: PlatformUserUpdatePayload }) =>
      platformUsersApi.update(id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: USERS_KEY })
      queryClient.invalidateQueries({
        queryKey: [...USERS_KEY, variables.id],
      })
    },
  })
}

export function useRemovePlatformUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => platformUsersApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USERS_KEY })
    },
  })
}

export function useResetPlatformUserPassword() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, new_password }: { id: number; new_password: string }) =>
      platformUsersApi.resetPassword(id, new_password),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...USERS_KEY, variables.id],
      })
    },
  })
}

export function useAssignPlatformUserTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: number
      payload: { tenant_id: number; role?: string; is_default?: boolean }
    }) => platformUsersApi.assignTenant(userId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: USERS_KEY })
      queryClient.invalidateQueries({
        queryKey: [...USERS_KEY, variables.userId],
      })
    },
  })
}

export function useRemovePlatformUserMembership() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      userId,
      membershipId,
    }: { userId: number; membershipId: number }) =>
      platformUsersApi.removeMembership(userId, membershipId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: USERS_KEY })
      queryClient.invalidateQueries({
        queryKey: [...USERS_KEY, variables.userId],
      })
    },
  })
}
