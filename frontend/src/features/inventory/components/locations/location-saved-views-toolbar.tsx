"use client"

import { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import {
  BookmarkIcon,
  ChevronDownIcon,
  Trash2Icon,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const STORAGE_KEY = "the-inventory.locations.savedViews.v1"

export type LocationSavedView = {
  id: string
  name: string
  search: string
  warehouseFilter: string
}

function loadViews(): LocationSavedView[] {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (v): v is LocationSavedView =>
        typeof v === "object" &&
        v !== null &&
        "id" in v &&
        "name" in v &&
        "search" in v &&
        "warehouseFilter" in v,
    )
  } catch {
    return []
  }
}

function storeViews(views: LocationSavedView[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(views))
}

function randomId(): string {
  return `v-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`
}

interface LocationSavedViewsToolbarProps {
  search: string
  warehouseFilter: string
  onApplyView: (view: LocationSavedView) => void
}

export function LocationSavedViewsToolbar({
  search,
  warehouseFilter,
  onApplyView,
}: LocationSavedViewsToolbarProps) {
  const t = useTranslations("Inventory")
  const [views, setViews] = useState<LocationSavedView[]>([])

  useEffect(() => {
    setViews(loadViews())
  }, [])

  const persist = useCallback((next: LocationSavedView[]) => {
    setViews(next)
    storeViews(next)
  }, [])

  const saveCurrent = useCallback(() => {
    const name = window.prompt(t("locations.savedViews.promptName"))
    if (name == null || !name.trim()) return
    const entry: LocationSavedView = {
      id: randomId(),
      name: name.trim(),
      search,
      warehouseFilter,
    }
    persist([...views, entry])
  }, [persist, search, t, views, warehouseFilter])

  const remove = useCallback(
    (id: string) => {
      persist(views.filter((v) => v.id !== id))
    },
    [persist, views],
  )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1"
          />
        }
      >
        <BookmarkIcon className="size-4" />
        <span className="max-w-[10rem] truncate">
          {t("locations.savedViews.trigger")}
        </span>
        <ChevronDownIcon className="size-3.5 opacity-60" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>
          {t("locations.savedViews.menuTitle")}
        </DropdownMenuLabel>
        <DropdownMenuItem onSelect={saveCurrent}>
          {t("locations.savedViews.saveCurrent")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {views.length === 0 ? (
          <div className="px-2 py-3 text-xs text-muted-foreground">
            {t("locations.savedViews.empty")}
          </div>
        ) : (
          views.map((v) => (
            <DropdownMenuItem
              key={v.id}
              className="flex items-center gap-2"
              onSelect={() => onApplyView(v)}
            >
              <span className="min-w-0 flex-1 truncate">{v.name}</span>
              <button
                type="button"
                className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-destructive"
                aria-label={t("locations.savedViews.removeAria", { name: v.name })}
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  remove(v.id)
                }}
              >
                <Trash2Icon className="size-3.5" />
              </button>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
