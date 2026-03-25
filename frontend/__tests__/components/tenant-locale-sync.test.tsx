import { cleanup, render, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { TenantLocaleSync } from "@/components/tenant-locale-sync"
import {
  DJANGO_LANGUAGE_COOKIE,
  LOCALE_USER_EXPLICIT_STORAGE_KEY,
} from "@/lib/locale-preference"

const routerReplace = vi.fn()
const routerRefresh = vi.fn()
const setApiUiLocale = vi.fn()

let mockLocale = "en"
const mockUseMe = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: routerRefresh }),
}))

vi.mock("next-intl", () => ({
  useLocale: () => mockLocale,
}))

vi.mock("@/i18n/navigation", () => ({
  usePathname: () => "/en/dashboard",
  useRouter: () => ({ replace: routerReplace }),
}))

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useMe: () => mockUseMe(),
}))

vi.mock("@/lib/api-ui-locale", () => ({
  setApiUiLocale: (...args: unknown[]) => setApiUiLocale(...args),
}))

describe("TenantLocaleSync", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    document.cookie = ""
    mockLocale = "en"
    mockUseMe.mockReturnValue({
      data: { tenant: { preferred_language: "fr" } },
      isSuccess: true,
    })
  })

  afterEach(() => {
    cleanup()
  })

  it("redirects and syncs cookie + API locale without setting explicit user storage", async () => {
    render(<TenantLocaleSync />)

    await waitFor(() => {
      expect(routerReplace).toHaveBeenCalledWith("/en/dashboard", { locale: "fr" })
      expect(routerRefresh).toHaveBeenCalled()
      expect(document.cookie).toContain(`${DJANGO_LANGUAGE_COOKIE}=fr`)
      expect(setApiUiLocale).toHaveBeenCalledWith("fr")
    })

    expect(localStorage.getItem(LOCALE_USER_EXPLICIT_STORAGE_KEY)).toBeNull()
  })

  it("does not redirect when an explicit locale preference exists", async () => {
    localStorage.setItem(LOCALE_USER_EXPLICIT_STORAGE_KEY, "en")

    render(<TenantLocaleSync />)

    await waitFor(() => {
      expect(routerReplace).not.toHaveBeenCalled()
      expect(setApiUiLocale).not.toHaveBeenCalled()
    })
  })

  it("runs again when tenant preferred_language changes (no explicit preference)", async () => {
    mockUseMe.mockReturnValueOnce({
      data: { tenant: { preferred_language: "fr" } },
      isSuccess: true,
    })
    const { rerender } = render(<TenantLocaleSync />)

    await waitFor(() => {
      expect(routerReplace).toHaveBeenCalledTimes(1)
    })

    mockLocale = "fr"
    mockUseMe.mockReturnValue({
      data: { tenant: { preferred_language: "sw" } },
      isSuccess: true,
    })
    rerender(<TenantLocaleSync />)

    await waitFor(() => {
      expect(routerReplace).toHaveBeenCalledWith("/en/dashboard", { locale: "sw" })
      expect(routerReplace).toHaveBeenCalledTimes(2)
    })
  })
})
