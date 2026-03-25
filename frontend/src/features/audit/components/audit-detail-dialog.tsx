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
import {
  AUDIT_ACTION_COLOR_MAP,
  getAuditActionLabel,
  isAuditAction,
} from "../helpers/audit-constants"

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
  const tActions = useTranslations("Audit.actionLabels")
  const tEventScope = useTranslations("Audit.eventScope")

  if (!entry) return null

  const colors = isAuditAction(entry.action)
    ? AUDIT_ACTION_COLOR_MAP[entry.action]
    : undefined
  const actionLabel = getAuditActionLabel(entry, (a) => tActions(a))
  const datetime = new Date(entry.timestamp).toLocaleString()
  const scope = entry.event_scope

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
              {actionLabel}
            </Badge>
          </Row>

          {entry.summary ? (
            <Row label={t("summary")}>
              <span className="text-right text-balance">{entry.summary}</span>
            </Row>
          ) : null}

          {scope ? (
            <Row label={t("eventScope")}>
              <Badge
                variant="outline"
                className={
                  scope === "platform"
                    ? "border-transparent bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300"
                    : "border-transparent bg-slate-100 text-slate-800 dark:bg-slate-800/40 dark:text-slate-300"
                }
              >
                {tEventScope(scope)}
              </Badge>
            </Row>
          ) : null}

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
