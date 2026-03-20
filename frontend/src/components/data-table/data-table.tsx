"use client"

import * as React from "react"
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  type PaginationState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  useReactTable,
} from "@tanstack/react-table"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { DataTablePagination } from "./data-table-pagination"
import { DataTableToolbar } from "./data-table-toolbar"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]

  pageCount?: number
  pagination?: PaginationState
  onPaginationChange?: (pagination: PaginationState) => void

  sorting?: SortingState
  onSortingChange?: (sorting: SortingState) => void

  searchKey?: string
  searchPlaceholder?: string
  searchValue?: string
  onSearchChange?: (value: string) => void
  filterContent?: React.ReactNode

  isLoading?: boolean
  emptyMessage?: string
  noResultsMessage?: string
}

export function DataTable<TData, TValue>({
  columns,
  data,
  pageCount,
  pagination: controlledPagination,
  onPaginationChange,
  sorting: controlledSorting,
  onSortingChange,
  searchKey,
  searchPlaceholder,
  searchValue,
  onSearchChange,
  filterContent,
  isLoading = false,
  emptyMessage,
  noResultsMessage,
}: DataTableProps<TData, TValue>) {
  const finalEmptyMessage = emptyMessage || noResultsMessage || "No results."
  const [sorting, setSorting] = React.useState<SortingState>(controlledSorting || [])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})

  const isServerPaginated = pageCount !== undefined && onPaginationChange !== undefined
  const isServerSorted = onSortingChange !== undefined

  const table = useReactTable({
    data,
    columns,
    pageCount: isServerPaginated ? pageCount : undefined,
    state: {
      sorting: controlledSorting !== undefined ? controlledSorting : sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      ...(isServerPaginated && controlledPagination
        ? { pagination: controlledPagination }
        : {}),
    },
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater
      if (isServerSorted && onSortingChange) {
        onSortingChange(next)
      } else {
        setSorting(next)
      }
    },
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    ...(isServerPaginated
      ? {
          manualPagination: true,
          onPaginationChange: (updater) => {
            const next =
              typeof updater === "function"
                ? updater(controlledPagination!)
                : updater
            onPaginationChange(next)
          },
        }
      : {}),
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  })

  return (
    <div className="space-y-4">
      <DataTableToolbar
        table={table}
        searchKey={searchKey}
        searchPlaceholder={searchPlaceholder}
        searchValue={searchValue}
        onSearchChange={onSearchChange}
      >
        {filterContent}
      </DataTableToolbar>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {columns.map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  {finalEmptyMessage}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination table={table} />
    </div>
  )
}
