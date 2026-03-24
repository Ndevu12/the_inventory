/**
 * Public registration screen rendering (feature shell).
 */
import type { ComponentProps } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RegisterCompanyPage } from "@/features/auth/pages/register-company-page";
import messages from "../../../public/locales/en.json";
import { clearQueryClientCache } from "@/lib/providers";
import {
  renderWithProviders,
  resetClientTestState,
  stubFetchAuthConfig,
} from "../../helpers/test-app-shell";

const { navigationState } = vi.hoisted(() => ({
  navigationState: { pathname: "/register" },
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

describe("RegisterCompanyPage rendering", () => {
  beforeEach(() => {
    navigationState.pathname = "/register";
    resetClientTestState();
    stubFetchAuthConfig(true);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    resetClientTestState();
  });

  it("renders the registration shell when public signup is enabled", async () => {
    clearQueryClientCache();
    renderWithProviders(
      <NextIntlClientProvider locale="en" messages={messages}>
        <RegisterCompanyPage />
      </NextIntlClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/create your organization/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/^organization name$/i)).toBeInTheDocument();
  });
});
