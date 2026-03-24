"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CycleStatus } from "../types/cycle-count.types";
import { CYCLE_STATUS_COLOR_MAP } from "../helpers/cycle-constants";

interface CycleStatusBadgeProps {
  status: CycleStatus;
  label?: string;
  className?: string;
}

export function CycleStatusBadge({
  status,
  label,
  className,
}: CycleStatusBadgeProps) {
  const t = useTranslations("CycleCounts.status");
  const colors = CYCLE_STATUS_COLOR_MAP[status];
  const displayLabel = label ?? t(status);

  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        colors.bg,
        colors.text,
        className,
      )}
    >
      {displayLabel}
    </Badge>
  );
}
