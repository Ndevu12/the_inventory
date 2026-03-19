"use client"

import type { Table } from "@tanstack/react-table"
import { XIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface DataTableToolbarProps<TData> {
  table: Table<TData>
  searchKey?: string
  searchPlaceholder?: string
  searchValue?: string
  onSearchChange?: (value: string) => void
  children?: React.ReactNode
}

export function DataTableToolbar<TData>({
  table,
  searchKey,
  searchPlaceholder = "Search...",
  searchValue,
  onSearchChange,
  children,
}: DataTableToolbarProps<TData>) {
  const isServerSearch = onSearchChange !== undefined
  const isFiltered = isServerSearch
    ? (searchValue?.length ?? 0) > 0
    : table.getState().columnFilters.length > 0

  const currentSearch = isServerSearch
    ? (searchValue ?? "")
    : searchKey
      ? (table.getColumn(searchKey)?.getFilterValue() as string) ?? ""
      : ""

  function handleSearchChange(value: string) {
    if (isServerSearch) {
      onSearchChange(value)
    } else if (searchKey) {
      table.getColumn(searchKey)?.setFilterValue(value)
    }
  }

  function handleReset() {
    if (isServerSearch) {
      onSearchChange("")
    }
    table.resetColumnFilters()
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-1 items-center space-x-2">
        {(searchKey || isServerSearch) && (
          <Input
            placeholder={searchPlaceholder}
            value={currentSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="h-8 w-[150px] lg:w-[250px]"
          />
        )}
        {children}
        {isFiltered && (
          <Button
            variant="ghost"
            onClick={handleReset}
            className="h-8 px-2 lg:px-3"
          >
            Reset
            <XIcon className="ml-2 size-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
