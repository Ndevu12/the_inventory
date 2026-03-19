import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { invitationsApi } from "../api/invitations-api"
import type {
  InvitationCreatePayload,
  PlatformInvitationListParams,
} from "../types/settings.types"

const INVITATIONS_KEY = ["tenant-invitations"] as const
const PLATFORM_INVITATIONS_KEY = ["platform-invitations"] as const

export function useInvitations() {
  return useQuery({
    queryKey: [...INVITATIONS_KEY],
    queryFn: () => invitationsApi.list(),
  })
}

export function useCreateInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: InvitationCreatePayload) =>
      invitationsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INVITATIONS_KEY })
    },
  })
}

export function useCancelInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => invitationsApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INVITATIONS_KEY })
    },
  })
}

export function useInvitationInfo(token: string) {
  return useQuery({
    queryKey: ["invitation-info", token],
    queryFn: () => invitationsApi.getInfo(token),
    enabled: !!token,
    retry: false,
  })
}

export function useAcceptInvitation(token: string) {
  return useMutation({
    mutationFn: (payload: Parameters<typeof invitationsApi.accept>[1]) =>
      invitationsApi.accept(token, payload),
  })
}

export function usePlatformInvitations(params?: PlatformInvitationListParams) {
  return useQuery({
    queryKey: [...PLATFORM_INVITATIONS_KEY, params],
    queryFn: () => invitationsApi.listPlatform(params),
  })
}

export function usePlatformCancelInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => invitationsApi.cancelPlatform(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PLATFORM_INVITATIONS_KEY })
    },
  })
}

export function usePlatformResendInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => invitationsApi.resendPlatform(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PLATFORM_INVITATIONS_KEY })
    },
  })
}
