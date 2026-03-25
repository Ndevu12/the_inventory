import { useAuthStore } from "@/lib/auth-store";

import type { MeResponse } from "../types/auth.types";

/** Keep Zustand in sync with GET /auth/me/ (shared by bootstrap + React Query). */
export function syncMeResponseToStore(data: MeResponse): void {
  const { setUser, setTenant, setMemberships } = useAuthStore.getState();
  setUser(data.user);
  if (data.tenant) {
    setTenant(data.tenant.slug);
  }
  setMemberships(data.memberships ?? []);
}
