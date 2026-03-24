import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import { vi } from "vitest";

import { clearQueryClientCache, Providers } from "@/lib/providers";
import { useAuthStore } from "@/lib/auth-store";

export function renderWithProviders(ui: ReactElement) {
  return render(<Providers>{ui}</Providers>);
}

/** Clears persisted auth, React Query cache, and localStorage between cases. */
export function resetClientTestState() {
  localStorage.clear();
  clearQueryClientCache();
  useAuthStore.getState().logout();
}

export function stubFetchAuthConfig(allowRegistration: boolean) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof Request
          ? input.url
          : String(input);
    if (url.includes("/auth/config/")) {
      return new Response(
        JSON.stringify({ allow_registration: allowRegistration }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    }
    return new Response(JSON.stringify({ detail: "unmocked" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  });
}
