import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi, beforeEach } from "vitest"

import { LanguageSwitcher } from "@/components/LanguageSwitcher"
import { DJANGO_LANGUAGE_COOKIE } from "@/lib/locale-preference"
import { routing } from "@/i18n/routing"

const routerReplace = vi.fn()
const routerRefresh = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: routerRefresh }),
}))

vi.mock("next-intl", () => ({
  useLocale: () => "en",
  useTranslations: (namespace: string) => {
    if (namespace === "LanguageSwitcher") {
      return (key: string) => (key === "ariaLabel" ? "Language" : key)
    }
    return (key: string) => key
  },
}))

vi.mock("@/i18n/navigation", () => ({
  usePathname: () => "/en/dashboard",
  useRouter: () => ({ replace: routerReplace }),
}))

describe("LanguageSwitcher", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    document.cookie = ""
  })

  afterEach(() => {
    cleanup()
  })

  it("lists every locale, then persists preference and navigates on change", async () => {
    const user = userEvent.setup()
    render(<LanguageSwitcher />)

    await user.click(screen.getByRole("button", { name: "Language" }))

    for (const code of routing.locales) {
      const label =
        {
          en: "English",
          fr: "French",
          sw: "Swahili",
          rw: "Kinyarwanda",
          es: "Spanish",
          ar: "Arabic",
        }[code] ?? code
      expect(await screen.findByRole("menuitemradio", { name: label })).toBeInTheDocument()
    }

    await user.click(screen.getByRole("menuitemradio", { name: "Spanish" }))

    await waitFor(() => {
      expect(document.cookie).toContain(`${DJANGO_LANGUAGE_COOKIE}=es`)
      expect(localStorage.getItem("the-inventory.locale")).toBe("es")
      expect(routerReplace).toHaveBeenCalledWith("/en/dashboard", { locale: "es" })
      expect(routerRefresh).toHaveBeenCalled()
    })
  })
})
