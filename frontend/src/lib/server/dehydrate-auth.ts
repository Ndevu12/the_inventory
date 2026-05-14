import { dehydrate, type DehydratedState } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import { authKeys } from "@/features/auth/auth-query-keys";
import type { MeResponse } from "@/features/auth/types/auth.types";

/**
 * Server-side utility to dehydrate auth state for RSC hydration.
 * Builds TanStack Query dehydrated payload with auth/me data.
 */
export function dehydrateAuthMe(
  queryClient: QueryClient,
  me: MeResponse | null,
): DehydratedState {
  if (me) {
    queryClient.setQueryData(authKeys.me, me);
  }
  return dehydrate(queryClient);
}
