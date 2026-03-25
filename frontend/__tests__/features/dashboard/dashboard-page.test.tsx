/**
 * Dashboard home rendering (feature shell); data hooks are mocked.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/features/dashboard/pages/dashboard-page";
import messages from "../../../public/locales/en.json";
import { useAuthStore } from "@/lib/auth-store";
import {
  renderWithProviders,
  resetClientTestState,
} from "../../helpers/test-app-shell";

vi.mock("@/features/dashboard/hooks/use-dashboard", () => {
  const q = () => ({
    data: undefined,
    isLoading: true,
    isError: false,
    error: null,
    refetch: vi.fn(),
  });
  return {
    useSummary: q,
    useStockByLocation: q,
    useMovementTrends: q,
    useOrderStatus: q,
    usePendingReservations: q,
    useExpiringLots: q,
  };
});

describe("DashboardPage rendering", () => {
  beforeEach(() => {
    resetClientTestState();
    useAuthStore.setState({
      accessToken: "fake-access",
      refreshToken: "fake-refresh",
      user: {
        id: 1,
        username: "demo",
        email: "demo@example.com",
        first_name: "",
        last_name: "",
        is_staff: true,
      },
      tenantSlug: "demo-tenant",
      memberships: [
        {
          tenant__id: 1,
          tenant__name: "Demo Org",
          tenant__slug: "demo-tenant",
          tenant__preferred_language: "en",
          role: "coordinator",
          is_default: true,
        },
      ],
      _hasHydrated: true,
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    resetClientTestState();
  });

  it("renders the dashboard shell with loading placeholders", async () => {
    renderWithProviders(
      <NextIntlClientProvider locale="en" messages={messages}>
        <DashboardPage />
      </NextIntlClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: messages.Dashboard.page.title,
        }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(messages.Dashboard.page.subtitle),
    ).toBeInTheDocument();
  });
});
