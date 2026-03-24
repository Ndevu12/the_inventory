"use client"

import * as React from "react"
import { useRouter } from "@/i18n/navigation"
import { useTranslations } from "next-intl"
import type { PaginationState } from "@tanstack/react-table"
import { DataTable } from "@/components/data-table/data-table"
import {
  DataTableFacetedFilter,
  type FacetedFilterOption,
} from "@/components/data-table/data-table-faceted-filter"
import {
  ArrowDownIcon,
  ArrowUpIcon,
  ArrowRightLeftIcon,
  SlidersHorizontalIcon,
} from "lucide-react"
import { useMovements } from "../../hooks/use-movements"
import { getMovementColumns } from "../../helpers/movement-columns"
import type { MovementListParams, StockMovement } from "../../api/movements-api"
import { MOVEMENT_TYPE_VALUES } from "../../helpers/movement-schemas"

const MOVEMENT_ICONS = {
  receive: ArrowDownIcon,
  issue: ArrowUpIcon,
  transfer: ArrowRightLeftIcon,
  adjustment: SlidersHorizontalIcon,
} as const

export function MovementTable() {
  const router = useRouter()
  const t = useTranslations("Inventory")

  const movementTypeOptions = React.useMemo<FacetedFilterOption[]>(
    () =>
      MOVEMENT_TYPE_VALUES.map((value) => ({
        label: t(`movementTypes.${value}`),
        value,
        icon: MOVEMENT_ICONS[value],
      })),
    [t],
  )

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [searchValue, setSearchValue] = React.useState("")
  const [typeFilter, setTypeFilter] = React.useState<string[]>([])

  const params = React.useMemo<MovementListParams>(() => {
    const p: MovementListParams = {
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      ordering: "-created_at",
      search: searchValue || undefined,
    }

    if (typeFilter.length === 1) {
      p.movement_type = typeFilter[0]
    }

    return p
  }, [pagination, searchValue, typeFilter])

  const { data, isLoading } = useMovements(params)

  const handleView = React.useCallback(
    (movement: StockMovement) => {
      router.push(`/stock/movements/${movement.id}`)
    },
    [router],
  )

  const columns = React.useMemo(
    () => getMovementColumns((key) => t(key as never), handleView),
    [handleView, t],
  )

  const pageCount = data
    ? Math.ceil(data.count / pagination.pageSize)
    : 0

  return (
    <DataTable
      columns={columns}
      data={data?.results ?? []}
      pageCount={pageCount}
      pagination={pagination}
      onPaginationChange={setPagination}
      searchValue={searchValue}
      onSearchChange={setSearchValue}
      searchPlaceholder={t("movements.searchPlaceholder")}
      isLoading={isLoading}
      emptyMessage={t("movements.empty")}
      filterContent={
        <MovementTypeFilter
          value={typeFilter}
          onChange={setTypeFilter}
          options={movementTypeOptions}
          title={t("filters.type")}
        />
      }
    />
  )
}

function MovementTypeFilter({
  value,
  onChange,
  options,
  title,
}: {
  value: string[]
  onChange: (value: string[]) => void
  options: FacetedFilterOption[]
  title: string
}) {
  const fakeColumn = React.useMemo(
    () =>
      ({
        id: "movement_type",
        getFacetedUniqueValues: () => new Map(),
        getFilterValue: () => value,
        setFilterValue: (val: unknown) => {
          onChange((val as string[] | undefined) ?? [])
        },
      }) as never,
    [value, onChange],
  )

  return (
    <DataTableFacetedFilter
      column={fakeColumn}
      title={title}
      options={options}
    />
  )
}
