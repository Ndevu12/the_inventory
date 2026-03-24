"use client"

import { useTranslations } from "next-intl"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TENANT_ROLE_VALUES } from "../helpers/settings-constants"
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
  const t = useTranslations("SettingsTenant.roles")

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
        {TENANT_ROLE_VALUES.map((role) => (
          <SelectItem key={role} value={role}>
            {t(role)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
