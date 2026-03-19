"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ROLE_OPTIONS } from "../helpers/settings-constants"
import type { TenantRole } from "../types/settings.types"

interface MemberRoleSelectProps {
  value: TenantRole
  onValueChange: (role: TenantRole) => void
  disabled?: boolean
}

export function MemberRoleSelect({
  value,
  onValueChange,
  disabled,
}: MemberRoleSelectProps) {
  return (
    <Select
      value={value}
      onValueChange={(val) => onValueChange(val as TenantRole)}
      disabled={disabled}
    >
      <SelectTrigger size="sm">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {ROLE_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
