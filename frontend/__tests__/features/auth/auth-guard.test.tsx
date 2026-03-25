/**
 * AuthGuard: bootstrap + membership gate for dashboard routes.
 */
import type { ReactElement } from "react";
import { cleanup, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthGuard } from "@/features/auth/components/auth-guard";
import messages from "../../../public/locales/en.json";
import { useAuthStore } from "@/lib/auth-store";
import {
  renderWithProviders,
  resetClientTestState,
} from "../../helpers/test-app-shell";

const { bootstrapProbe, routerReplace } = vi.hoisted(() => ({
  bootstrapProbe: { isFetched: false, isError: false },
  routerReplace: vi.fn(),
}));

vi.mock("@/i18n/navigation", () => ({
  useRouter: () => ({ replace: routerReplace, push: vi.fn() }),
}));

vi.mock("@/features/auth/hooks/use-auth", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/auth/hooks/use-auth")>();
  return {
    ...actual,
    useBootstrapAuth: () => ({
      isFetched: bootstrapProbe.isFetched,
      isError: bootstrapProbe.isError,
      error: null,
    }),
  };
});

function renderGuard(ui: ReactElement) {
  return renderWithProviders(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("AuthGuard", () => {
  beforeEach(() => {
    resetClientTestState();
    routerReplace.mockClear();
    bootstrapProbe.isFetched = false;
    bootstrapProbe.isError = false;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    resetClientTestState();
  });

  it("redirects to login when there is no token", async () => {
    useAuthStore.setState({
      _hasHydrated: true,
    });

    renderGuard(
      <AuthGuard>
        <span data-testid="child">inside</span>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(routerReplace).toHaveBeenCalledWith("/login");
    });
    expect(screen.queryByTestId("child")).not.toBeInTheDocument();
  });

  it("redirects to no-organization when bootstrap succeeded with zero memberships", async () => {
    bootstrapProbe.isFetched = true;
    bootstrapProbe.isError = false;
    useAuthStore.setState({
      accessToken: "access",
      refreshToken: "refresh",
      user: {
        id: 1,
        username: "solo",
        email: "solo@example.com",
        first_name: "",
        last_name: "",
        is_staff: false,
      },
      tenantSlug: null,
      memberships: [],
      _hasHydrated: true,
    });

    renderGuard(
      <AuthGuard>
        <span data-testid="child">inside</span>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(routerReplace).toHaveBeenCalledWith("/no-organization");
    });
    expect(screen.queryByTestId("child")).not.toBeInTheDocument();
  });

  it("renders children when authenticated and at least one membership", async () => {
    bootstrapProbe.isFetched = true;
    bootstrapProbe.isError = false;
    useAuthStore.setState({
      accessToken: "valid-access-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      refreshToken: "refresh",
      user: {
        id: 1,
        username: "member",
        email: "member@example.com",
        first_name: "",
        last_name: "",
        is_staff: false,
      },
      tenantSlug: "acme",
      memberships: [
        {
          tenant__id: 1,
          tenant__name: "Acme",
          tenant__slug: "acme",
          role: "owner",
          is_default: true,
        },
      ],
      _hasHydrated: true,
    });

    renderGuard(
      <AuthGuard>
        <span data-testid="child">inside</span>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("child")).toBeInTheDocument();
    });
    expect(routerReplace).not.toHaveBeenCalled();
  });

  it("allows dashboard when user has memberships even if also staff/superuser (WS12)", async () => {
    bootstrapProbe.isFetched = true;
    bootstrapProbe.isError = false;
    useAuthStore.setState({
      accessToken:
        "valid-access-token-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
      refreshToken: "refresh",
      user: {
        id: 1,
        username: "dual",
        email: "dual@example.com",
        first_name: "",
        last_name: "",
        is_staff: true,
        is_superuser: true,
      },
      tenantSlug: "acme",
      memberships: [
        {
          tenant__id: 1,
          tenant__name: "Acme",
          tenant__slug: "acme",
          role: "coordinator",
          is_default: true,
        },
      ],
      _hasHydrated: true,
    });

    renderGuard(
      <AuthGuard>
        <span data-testid="child">inside</span>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("child")).toBeInTheDocument();
    });
    expect(routerReplace).not.toHaveBeenCalled();
  });
});
