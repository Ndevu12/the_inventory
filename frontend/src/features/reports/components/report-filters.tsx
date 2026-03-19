"use client"

import * as React from "react"
import { format as formatDateFn } from "date-fns"
import { CalendarIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

// --- Date Range Picker ---

interface DateRangeFilterProps {
  dateFrom: string
  dateTo: string
  onDateFromChange: (value: string) => void
  onDateToChange: (value: string) => void
}

export function DateRangeFilter({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: DateRangeFilterProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <DatePickerField
        label="From"
        value={dateFrom}
        onChange={onDateFromChange}
      />
      <DatePickerField
        label="To"
        value={dateTo}
        onChange={onDateToChange}
      />
    </div>
  )
}

interface DatePickerFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
}

function DatePickerField({ label, value, onChange }: DatePickerFieldProps) {
  const date = value ? new Date(value) : undefined

  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Popover>
        <PopoverTrigger render={<Button variant="outline" className={cn("w-[180px] justify-start text-left font-normal", !date && "text-muted-foreground")} />}>
          <CalendarIcon className="mr-2 size-4" />
          {date ? formatDateFn(date, "MMM d, yyyy") : "Pick a date"}
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={date}
            onSelect={(d) => onChange(d ? formatDateFn(d, "yyyy-MM-dd") : "")}
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}

// --- Select Filter ---

interface SelectFilterProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
}

export function SelectFilter({
  label,
  value,
  onChange,
  options,
  placeholder = "All",
}: SelectFilterProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Select
        value={value || undefined}
        onValueChange={(val) => onChange(val === "__all__" ? "" : (val ?? ""))}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">{placeholder}</SelectItem>
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

// --- Number Input Filter ---

interface NumberFilterProps {
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
}

export function NumberFilter({
  label,
  value,
  onChange,
  min = 1,
  max,
}: NumberFilterProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input
        type="number"
        className="w-[100px]"
        value={value}
        min={min}
        max={max}
        onChange={(e) => {
          const n = parseInt(e.target.value, 10)
          if (!isNaN(n)) onChange(n)
        }}
      />
    </div>
  )
}

// --- Text Input Filter ---

interface TextFilterProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function TextFilter({
  label,
  value,
  onChange,
  placeholder,
}: TextFilterProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input
        className="w-[180px]"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  )
}
