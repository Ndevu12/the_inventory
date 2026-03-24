/**
 * Login screen rendering (feature shell), not root `Providers` wiring.
 */
import type { ComponentProps } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/pages/login-page";
import messages from "../../../public/locales/en.json";
import {
  renderWithProviders,
  resetClientTestState,
  stubFetchAuthConfig,
} from "../../helpers/test-app-shell";

const { navigationState } = vi.hoisted(() => ({
  navigationState: { pathname: "/login" },
}));

vi.mock("@/i18n/navigation", () => ({
  Link: ({
    href,
    children,
    ...rest
  }: ComponentProps<"a"> & { href: string }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => navigationState.pathname,
}));

describe("LoginPage rendering", () => {
  beforeEach(() => {
    navigationState.pathname = "/login";
    resetClientTestState();
    stubFetchAuthConfig(false);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    resetClientTestState();
  });

  it("renders the login shell inside Providers", async () => {
    renderWithProviders(
      <NextIntlClientProvider locale="en" messages={messages}>
        <LoginPage />
      </NextIntlClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
});
