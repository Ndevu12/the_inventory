/**
 * Root client entry only: same `Providers` tree as `app/[locale]/layout.tsx`.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearQueryClientCache, Providers } from "@/lib/providers";
import { useAuthStore } from "@/lib/auth-store";

describe("root provider entry", () => {
  beforeEach(() => {
    localStorage.clear();
    clearQueryClientCache();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    useAuthStore.getState().logout();
    clearQueryClientCache();
  });

  it("hydrates AuthProvider and renders children (main app mount path)", async () => {
    render(
      <Providers>
        <main data-testid="root-app-entry">Mounted</main>
      </Providers>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("root-app-entry")).toBeVisible();
    });

    expect(screen.getByText("Mounted")).toBeInTheDocument();
    expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
  });

  it("mounts global toast notifications from the root shell", async () => {
    render(
      <Providers>
        <span data-testid="root-app-entry">x</span>
      </Providers>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("root-app-entry")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("region", { name: /notifications/i }),
    ).toBeInTheDocument();
  });
});
