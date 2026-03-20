import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

/** No-op storage for SSR; localStorage is undefined in Node. Prevents crashes and hydration issues. */
const noopStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser?: boolean;
}

export interface TenantInfo {
  id: number;
  name: string;
  slug: string;
  role: string | null;
}

export interface Membership {
  tenant__id: number;
  tenant__name: string;
  tenant__slug: string;
  role: string;
  is_default: boolean;
}

export interface ImpersonationState {
  real_user: User;
  real_access_token: string;
  real_refresh_token: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  tenantSlug: string | null;
  memberships: Membership[];
  /** Set when impersonating; stores real user's data for "Exit impersonation". */
  impersonation: ImpersonationState | null;
  /** True after persist has loaded from localStorage (client-only). Prevents redirect loops. */
  _hasHydrated: boolean;
}

interface AuthActions {
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  setTenant: (slug: string) => void;
  setMemberships: (memberships: Membership[]) => void;
  setImpersonation: (data: ImpersonationState | null) => void;
  logout: () => void;
  exitImpersonation: () => void;
  isAuthenticated: () => boolean;
  isImpersonating: () => boolean;
}

const initialState: AuthState = {
  accessToken: null,
  refreshToken: null,
  user: null,
  tenantSlug: null,
  memberships: [],
  impersonation: null,
  _hasHydrated: false,
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),

      setUser: (user) => set({ user }),

      setTenant: (slug) => set({ tenantSlug: slug }),

      setMemberships: (memberships) => set({ memberships }),

      setImpersonation: (data) => set({ impersonation: data }),

      logout: () =>
        set({
          ...initialState,
          _hasHydrated: get()._hasHydrated,
        }),

      exitImpersonation: () => {
        const imp = get().impersonation;
        if (imp) {
          set({
            accessToken: imp.real_access_token,
            refreshToken: imp.real_refresh_token,
            impersonation: null,
          });
        }
      },

      isAuthenticated: () => get().accessToken !== null,
      isImpersonating: () => get().impersonation !== null,
    }),
    {
      name: "inventory-auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : noopStorage,
      ),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        tenantSlug: state.tenantSlug,
        memberships: state.memberships,
        impersonation: state.impersonation,
      }),
      onRehydrateStorage: () => () => {
        setTimeout(() => {
          useAuthStore.setState({ _hasHydrated: true });
        }, 0);
      },
    },
  ),
);
