import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query"
import { membersApi } from "../api/members-api"
import type {
  MemberListParams,
  MemberUpdatePayload,
} from "../types/settings.types"

const MEMBERS_KEY = ["tenant-members"] as const

export function useMembers(params?: MemberListParams) {
  return useQuery({
    queryKey: [...MEMBERS_KEY, params],
    queryFn: () => membersApi.list(params),
  })
}

export function useMember(id: number) {
  return useQuery({
    queryKey: [...MEMBERS_KEY, id],
    queryFn: () => membersApi.get(id),
    enabled: id > 0,
  })
}

export function useUpdateMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number
      payload: MemberUpdatePayload
    }) => membersApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMBERS_KEY })
    },
  })
}

export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => membersApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMBERS_KEY })
    },
  })
}
