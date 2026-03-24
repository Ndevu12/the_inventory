"use client"

import { useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { AuditEntry } from "../types/audit.types"
import { AUDIT_ACTION_COLOR_MAP } from "../helpers/audit-constants"

interface AuditDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  entry: AuditEntry | null
}

export function AuditDetailDialog({
  open,
  onOpenChange,
  entry,
}: AuditDetailDialogProps) {
  const t = useTranslations("Audit.detail")
  const tAudit = useTranslations("Audit")

  if (!entry) return null

  const colors = AUDIT_ACTION_COLOR_MAP[entry.action]
  const datetime = new Date(entry.timestamp).toLocaleString()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title", { id: entry.id })}</DialogTitle>
          <DialogDescription>
            {t("recordedOn", { datetime })}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 text-sm">
          <Row label={t("action")}>
            <Badge
              variant="outline"
              className={`${colors?.bg ?? ""} ${colors?.text ?? ""} border-transparent`}
            >
              {entry.action_display}
            </Badge>
          </Row>

          <Row label={t("product")}>
            {entry.product_name ? (
              <span>
                {entry.product_name}
                {entry.product_sku && (
                  <span className="ml-1 text-muted-foreground">
                    ({entry.product_sku})
                  </span>
                )}
              </span>
            ) : (
              <span className="text-muted-foreground">{tAudit("emDash")}</span>
            )}
          </Row>

          <Row label={t("user")}>
            {entry.username ?? (
              <span className="text-muted-foreground">{tAudit("system")}</span>
            )}
          </Row>

          <Row label={t("ipAddress")}>
            {entry.ip_address ?? (
              <span className="text-muted-foreground">{tAudit("emDash")}</span>
            )}
          </Row>

          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {t("detailsJson")}
            </span>
            <ScrollArea className="h-[200px] rounded-md border bg-muted/40 p-3">
              <pre className="text-xs leading-relaxed whitespace-pre-wrap break-all font-mono">
                {JSON.stringify(entry.details, null, 2)}
              </pre>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}

function Row({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider shrink-0">
        {label}
      </span>
      <span className="text-right">{children}</span>
    </div>
  )
}
