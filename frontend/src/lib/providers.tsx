"use client";

import {
  dehydrate,
  HydrationBoundary,
  QueryClientProvider,
  type DehydratedState,
} from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { authKeys } from "@/features/auth/auth-query-keys";
import { AuthProvider } from "@/features/auth/context/auth-context";
import type { MeResponse } from "@/features/auth/types/auth.types";
import { makeQueryClient } from "./query-client";

let browserQueryClient: ReturnType<typeof makeQueryClient> | undefined;

function getQueryClient() {
  if (typeof window === "undefined") {
    return makeQueryClient();
  }
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }
  return browserQueryClient;
}

/** Clears the browser QueryClient cache (e.g. between Vitest cases that share Providers). */
export function clearQueryClientCache(): void {
  browserQueryClient?.clear();
}

/** Build TanStack dehydrate payload for RSC (per-request QueryClient). */
export function dehydrateAuthMe(
  queryClient: ReturnType<typeof makeQueryClient>,
  me: MeResponse | null,
): DehydratedState {
  if (me) {
    queryClient.setQueryData(authKeys.me, me);
  }
  return dehydrate(queryClient);
}

export function Providers({
  children,
  dehydratedState,
  serverBootstrap,
}: {
  children: React.ReactNode;
  dehydratedState?: DehydratedState;
  serverBootstrap?: MeResponse | null;
}) {
  const queryClient = getQueryClient();

  const tree = (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <TooltipProvider>
        <AuthProvider serverBootstrap={serverBootstrap}>{children}</AuthProvider>
      </TooltipProvider>
      <Toaster richColors closeButton position="bottom-right" />
    </ThemeProvider>
  );

  return (
    <QueryClientProvider client={queryClient}>
      {dehydratedState ? (
        <HydrationBoundary state={dehydratedState}>{tree}</HydrationBoundary>
      ) : (
        tree
      )}
    </QueryClientProvider>
  );
}
