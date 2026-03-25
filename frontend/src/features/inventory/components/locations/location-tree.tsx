"use client"

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react"
import { useVirtualizer } from "@tanstack/react-virtual"
import { useTranslations } from "next-intl"
import {
  ChevronRightIcon,
  PencilIcon,
  Trash2Icon,
  WarehouseIcon,
} from "lucide-react"
import { toast } from "sonner"
import { Link } from "@/i18n/navigation"
import { cn } from "@/lib/utils"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useDeleteLocation } from "../../hooks/use-locations"
import type { StockLocation } from "../../types/location.types"

export type LocationTreeHandle = {
  /** Expand site group + tree ancestors, then scroll the row into view. */
  revealLocation: (locationId: number, ancestorIds: number[]) => void
}

type TreeRow =
  | { kind: "group"; groupKey: string; title: string; count: number }
  | {
      kind: "location"
      location: StockLocation
      depthIndent: number
      hasChildren: boolean
    }

function groupLocations(
  locations: StockLocation[],
): Map<string, StockLocation[]> {
  const map = new Map<string, StockLocation[]>()
  for (const loc of locations) {
    const key = loc.warehouse_id != null ? `w:${loc.warehouse_id}` : "retail"
    const list = map.get(key) ?? []
    list.push(loc)
    map.set(key, list)
  }
  for (const [, list] of map) {
    list.sort(sortLocationsByTreeOrder)
  }
  return map
}

function sortLocationsByTreeOrder(a: StockLocation, b: StockLocation) {
  const pa = a.materialized_path ?? ""
  const pb = b.materialized_path ?? ""
  if (pa && pb) return pa.localeCompare(pb)
  const da = a.depth ?? 1
  const db = b.depth ?? 1
  if (da !== db) return da - db
  return a.name.localeCompare(b.name)
}

function shallowestDepthInGroup(groupLocationsList: StockLocation[]): number {
  const depths = groupLocationsList
    .map((l) => l.depth)
    .filter((d): d is number => typeof d === "number" && Number.isFinite(d))
  if (!depths.length) return 1
  return Math.min(...depths)
}

/** Indent from treebeard ``depth`` within this site group when the API sends it; otherwise fall back to parent/child walk depth. */
function buildHierarchyRows(
  groupLocationsList: StockLocation[],
  collapsedTreeNodes: Set<number>,
): Omit<Extract<TreeRow, { kind: "location" }>, "kind">[] {
  const minDepth = shallowestDepthInGroup(groupLocationsList)
  const hasMpDepth = groupLocationsList.some(
    (l) => l.depth != null && Number.isFinite(l.depth),
  )
  const byId = new Map(groupLocationsList.map((l) => [l.id, l]))
  const children = new Map<number | null, StockLocation[]>()
  for (const loc of groupLocationsList) {
    let p: number | null = loc.parent_id ?? null
    if (p != null && !byId.has(p)) p = null
    const list = children.get(p) ?? []
    list.push(loc)
    children.set(p, list)
  }
  for (const [, list] of children) {
    list.sort(sortLocationsByTreeOrder)
  }

  const out: Omit<Extract<TreeRow, { kind: "location" }>, "kind">[] = []

  function walk(parentKey: number | null, walkDepth: number) {
    const kids = children.get(parentKey) ?? []
    for (const loc of kids) {
      const hasCh = (children.get(loc.id)?.length ?? 0) > 0
      const depthIndent = hasMpDepth
        ? Math.max(0, (loc.depth ?? minDepth) - minDepth)
        : walkDepth
      out.push({ location: loc, depthIndent, hasChildren: hasCh })
      if (hasCh && !collapsedTreeNodes.has(loc.id)) {
        walk(loc.id, walkDepth + 1)
      }
    }
  }
  walk(null, 0)
  return out
}

function sortGroupEntries(map: Map<string, StockLocation[]>) {
  return [...map.entries()].sort(([ka], [kb]) => {
    const isRetailA = ka === "retail"
    const isRetailB = kb === "retail"
    if (isRetailA && !isRetailB) return 1
    if (!isRetailA && isRetailB) return -1
    const locA = map.get(ka)![0]
    const locB = map.get(kb)![0]
    const nameA = locA.warehouse?.name ?? ""
    const nameB = locB.warehouse?.name ?? ""
    return nameA.localeCompare(nameB)
  })
}

function buildRows(
  locations: StockLocation[],
  showSiteGroups: boolean,
  collapsedGroups: Set<string>,
  collapsedTreeNodes: Set<number>,
  titleForGroup: (groupKey: string, sample: StockLocation | undefined) => string,
): TreeRow[] {
  const map = groupLocations(locations)
  const entries = sortGroupEntries(map)

  const rows: TreeRow[] = []
  for (const [groupKey, locs] of entries) {
    if (showSiteGroups) {
      rows.push({
        kind: "group",
        groupKey,
        title: titleForGroup(groupKey, locs[0]),
        count: locs.length,
      })
      if (!collapsedGroups.has(groupKey)) {
        const hier = buildHierarchyRows(locs, collapsedTreeNodes)
        for (const h of hier) {
          rows.push({ kind: "location", ...h })
        }
      }
    } else {
      const hier = buildHierarchyRows(locs, collapsedTreeNodes)
      for (const h of hier) {
        rows.push({ kind: "location", ...h })
      }
    }
  }
  return rows
}

function utilizationPercent(location: StockLocation): number | null {
  if (location.max_capacity === null || location.max_capacity <= 0) return null
  return Math.min(
    (location.current_utilization / location.max_capacity) * 100,
    100,
  )
}

interface CompactLocationRowProps {
  location: StockLocation
  onEdit: (location: StockLocation) => void
  depthIndent: number
  hasChildren: boolean
  treeCollapsed: boolean
  onToggleTree: () => void
}

function CompactLocationRow({
  location,
  onEdit,
  depthIndent,
  hasChildren,
  treeCollapsed,
  onToggleTree,
}: CompactLocationRowProps) {
  const t = useTranslations("Inventory")
  const tCommon = useTranslations("Common.actions")
  const tCommonStates = useTranslations("Common.states")
  const [deleteOpen, setDeleteOpen] = useState(false)
  const deleteMutation = useDeleteLocation()
  const pct = utilizationPercent(location)

  const confirmDelete = () => {
    deleteMutation.mutate(location.id, {
      onSuccess: () => {
        toast.success(t("locations.toastDeleted", { name: location.name }))
        setDeleteOpen(false)
      },
      onError: (err) =>
        toast.error(err.message || t("locations.toastDeleteFailed")),
    })
  }

  const indentPx = depthIndent * 14

  return (
    <div className="border-b bg-card last:border-b-0">
      <div
        className={cn(
          "group/row flex w-full items-center gap-2 px-2 py-1.5",
        )}
      >
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center",
            !hasChildren && "pointer-events-none",
          )}
        >
          {hasChildren ? (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="size-8 shrink-0"
              onClick={onToggleTree}
              aria-expanded={!treeCollapsed}
              aria-label={
                treeCollapsed
                  ? t("locations.list.expandBranch")
                  : t("locations.list.collapseBranch")
              }
            >
              <ChevronRightIcon
                className={cn(
                  "size-4 transition-transform duration-200",
                  !treeCollapsed && "rotate-90",
                )}
              />
            </Button>
          ) : (
            <span
              className="size-1.5 rounded-full bg-muted-foreground/35"
              aria-hidden
            />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <Link
            href={`/stock/locations/${location.id}`}
            className={cn(
              "flex min-w-0 items-center gap-2 rounded-md py-0.5 pl-2 pr-1 outline-offset-2 hover:bg-muted/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring",
              depthIndent > 0 && "border-l border-border/70",
            )}
            style={{ marginLeft: indentPx }}
            aria-label={t("locations.list.openDetailAria", {
              name: location.name,
            })}
          >
            <div className="min-w-0 flex-1">
              <div className="flex min-w-0 items-center gap-2">
                <span className="truncate text-sm font-medium">
                  {location.name}
                </span>
                <Badge
                  variant={location.is_active ? "default" : "secondary"}
                  className="hidden shrink-0 text-[10px] sm:inline-flex"
                >
                  {location.is_active ? t("shared.active") : t("shared.inactive")}
                </Badge>
              </div>
              {location.description ? (
                <p className="truncate text-xs text-muted-foreground">
                  {location.description}
                </p>
              ) : null}
            </div>
            <ChevronRightIcon
              className="size-4 shrink-0 text-muted-foreground opacity-40 transition-opacity group-hover/row:opacity-80"
              aria-hidden
            />
          </Link>
        </div>

        <div className="hidden w-[5.5rem] shrink-0 text-right text-xs tabular-nums text-muted-foreground sm:block">
          {pct != null
            ? t("locations.capacity.percent", { pct: Math.round(pct) })
            : t("locations.list.utilUnlimited", {
                count: location.current_utilization,
              })}
        </div>

        <Badge
          variant={location.is_active ? "default" : "secondary"}
          className="shrink-0 text-[10px] sm:hidden"
        >
          {location.is_active ? t("shared.active") : t("shared.inactive")}
        </Badge>

        <div className="flex w-[4.5rem] shrink-0 justify-end gap-0.5">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="size-8"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onEdit(location)
            }}
            aria-label={t("shared.editLocation")}
          >
            <PencilIcon className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="size-8"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              setDeleteOpen(true)
            }}
            disabled={deleteMutation.isPending}
            aria-label={t("shared.deleteLocation")}
          >
            <Trash2Icon className="size-4" />
          </Button>
        </div>
      </div>

      <AlertDialog
        open={deleteOpen}
        onOpenChange={(open) => {
          setDeleteOpen(open)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("locations.deleteDialogTitle")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("shared.confirmDeleteLocation", { name: location.name })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>
              {tCommon("cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending
                ? tCommonStates("loading")
                : tCommon("delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

interface LocationTreeProps {
  locations: StockLocation[]
  /** When false (site filter is not “all”), hide facility group headers so the strip + filter carry site context. */
  showSiteGroups?: boolean
  onEdit: (location: StockLocation) => void
  isLoading?: boolean
  hasNextPage?: boolean
  isFetchingNextPage?: boolean
  fetchNextPage?: () => void
  totalCount?: number
}

export const LocationTree = forwardRef<LocationTreeHandle, LocationTreeProps>(
  function LocationTree(
    {
      locations,
      showSiteGroups = true,
      onEdit,
      isLoading,
      hasNextPage,
      isFetchingNextPage,
      fetchNextPage,
      totalCount,
    },
    ref,
  ) {
    const t = useTranslations("Inventory")
    const scrollRef = useRef<HTMLDivElement>(null)
    const sentinelRef = useRef<HTMLDivElement>(null)
    const locationsRef = useRef(locations)
    locationsRef.current = locations

    const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
      () => new Set(),
    )
    const [collapsedTreeNodes, setCollapsedTreeNodes] = useState<Set<number>>(
      () => new Set(),
    )
    const [pendingScrollToId, setPendingScrollToId] = useState<number | null>(
      null,
    )

    const titleForGroup = useCallback(
      (groupKey: string, sample: StockLocation | undefined) => {
        if (groupKey === "retail") return t("locations.siteGroup.storeRetail")
        return sample?.warehouse?.name ?? t("locations.siteGroup.unknownFacility")
      },
      [t],
    )

    const rows = useMemo(
      () =>
        buildRows(
          locations,
          showSiteGroups,
          collapsedGroups,
          collapsedTreeNodes,
          titleForGroup,
        ),
      [
        locations,
        showSiteGroups,
        collapsedGroups,
        collapsedTreeNodes,
        titleForGroup,
      ],
    )

    const virtualizer = useVirtualizer({
      count: rows.length,
      getScrollElement: () => scrollRef.current,
      estimateSize: (index) => {
        const row = rows[index]
        if (!row) return 44
        if (row.kind === "group") return 40
        return 44
      },
      overscan: 8,
      getItemKey: (index) => {
        const row = rows[index]
        if (!row) return String(index)
        if (row.kind === "group") return `g:${row.groupKey}`
        return `l:${row.location.id}`
      },
    })

    const revealLocation = useCallback(
      (locationId: number, ancestorIds: number[]) => {
        const locs = locationsRef.current
        const loc = locs.find((l) => l.id === locationId)
        setCollapsedGroups((prev) => {
          const next = new Set(prev)
          if (loc) {
            const gk =
              loc.warehouse_id != null ? `w:${loc.warehouse_id}` : "retail"
            next.delete(gk)
          }
          return next
        })
        setCollapsedTreeNodes((prev) => {
          const next = new Set(prev)
          for (const aid of ancestorIds) next.delete(aid)
          return next
        })
        setPendingScrollToId(locationId)
      },
      [],
    )

    useImperativeHandle(ref, () => ({ revealLocation }), [revealLocation])

    useEffect(() => {
      virtualizer.measure()
    }, [collapsedGroups, collapsedTreeNodes, rows.length, virtualizer])

    useEffect(() => {
      const root = scrollRef.current
      const sentinel = sentinelRef.current
      if (!root || !sentinel || !hasNextPage || !fetchNextPage) return

      const obs = new IntersectionObserver(
        (entries) => {
          const hit = entries.some((e) => e.isIntersecting)
          if (hit) fetchNextPage()
        },
        { root, rootMargin: "120px", threshold: 0 },
      )
      obs.observe(sentinel)
      return () => obs.disconnect()
    }, [hasNextPage, fetchNextPage, locations.length])

    useEffect(() => {
      if (pendingScrollToId == null) return
      const id = pendingScrollToId
      const idx = rows.findIndex(
        (r) => r.kind === "location" && r.location.id === id,
      )
      if (idx >= 0) {
        virtualizer.scrollToIndex(idx, { align: "center" })
        setPendingScrollToId(null)
        return
      }
      if (!locations.some((l) => l.id === id)) {
        setPendingScrollToId(null)
      }
    }, [pendingScrollToId, rows, virtualizer, locations])

    const toggleGroup = (groupKey: string) => {
      setCollapsedGroups((prev) => {
        const next = new Set(prev)
        if (next.has(groupKey)) next.delete(groupKey)
        else next.add(groupKey)
        return next
      })
    }

    const toggleTreeNode = (nodeId: number) => {
      setCollapsedTreeNodes((prev) => {
        const next = new Set(prev)
        if (next.has(nodeId)) next.delete(nodeId)
        else next.add(nodeId)
        return next
      })
    }

    if (isLoading) {
      return (
        <div className="space-y-2 rounded-md border p-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      )
    }

    if (!locations.length) {
      return (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
          <WarehouseIcon className="mb-4 size-12 text-muted-foreground/50" />
          <h3 className="text-lg font-medium">{t("locations.emptyTitle")}</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("locations.emptyDescription")}
          </p>
        </div>
      )
    }

    const loaded = locations.length
    const total = totalCount ?? loaded

    return (
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>{t("locations.list.loadedSummary", { loaded, total })}</span>
          <span className="hidden sm:inline">
            {t("locations.list.hintScroll")}
          </span>
        </div>

        <div
          ref={scrollRef}
          className="max-h-[min(70vh,560px)] overflow-auto rounded-md border"
        >
          <div className="sticky top-0 z-10 flex w-full items-center gap-2 border-b bg-muted/95 px-2 py-2 text-xs font-medium backdrop-blur-sm">
            <span className="sr-only w-8 shrink-0">
              {t("locations.list.colExpand")}
            </span>
            <div className="w-8 shrink-0" aria-hidden />
            <span className="min-w-0 flex-1">{t("locations.list.colLocation")}</span>
            <span className="hidden w-[5.5rem] shrink-0 text-right sm:block">
              {t("locations.list.colUtilization")}
            </span>
            <span className="w-[4.5rem] shrink-0 text-right">
              {t("locations.list.colActions")}
            </span>
          </div>

          <div
            className="relative w-full"
            style={{
              height: `${virtualizer.getTotalSize() + (hasNextPage ? 40 : 0)}px`,
            }}
          >
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index]
              if (!row) return null

              if (row.kind === "group") {
                const collapsed = collapsedGroups.has(row.groupKey)
                return (
                  <div
                    key={virtualRow.key}
                    data-index={virtualRow.index}
                    ref={virtualizer.measureElement}
                    className="absolute left-0 top-0 w-full border-b bg-muted/30"
                    style={{
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-2 py-2 text-left text-sm font-medium hover:bg-muted/50"
                      onClick={() => toggleGroup(row.groupKey)}
                      aria-expanded={!collapsed}
                      aria-label={
                        collapsed
                          ? t("locations.list.expandSite", { name: row.title })
                          : t("locations.list.collapseSite", { name: row.title })
                      }
                    >
                      <ChevronRightIcon
                        className={cn(
                          "size-4 shrink-0 transition-transform",
                          !collapsed && "rotate-90",
                        )}
                      />
                      <span className="truncate">{row.title}</span>
                      <span className="ml-auto shrink-0 tabular-nums text-xs font-normal text-muted-foreground">
                        {t("locations.list.groupLocationCount", {
                          count: row.count,
                        })}
                      </span>
                    </button>
                  </div>
                )
              }

              const loc = row.location
              const treeCollapsed = collapsedTreeNodes.has(loc.id)

              return (
                <div
                  key={virtualRow.key}
                  data-index={virtualRow.index}
                  data-location-id={loc.id}
                  ref={virtualizer.measureElement}
                  className="absolute left-0 top-0 w-full"
                  style={{
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <CompactLocationRow
                    location={loc}
                    onEdit={onEdit}
                    depthIndent={row.depthIndent}
                    hasChildren={row.hasChildren}
                    treeCollapsed={treeCollapsed}
                    onToggleTree={() => toggleTreeNode(loc.id)}
                  />
                </div>
              )
            })}

            {hasNextPage ? (
              <div
                ref={sentinelRef}
                className="absolute left-0 flex w-full items-center justify-center py-2 text-xs text-muted-foreground"
                style={{
                  transform: `translateY(${virtualizer.getTotalSize()}px)`,
                }}
              >
                {isFetchingNextPage ? t("locations.list.loadingMore") : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    )
  },
)

LocationTree.displayName = "LocationTree"
