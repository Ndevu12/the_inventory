"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ReservationStatus } from "../types/reservation.types";
import { STATUS_COLOR_MAP } from "../helpers/reservation-constants";

interface ReservationStatusBadgeProps {
  status: ReservationStatus;
  label?: string;
  className?: string;
}

export function ReservationStatusBadge({
  status,
  label,
  className,
}: ReservationStatusBadgeProps) {
  const t = useTranslations("Reservations.status");
  const colors = STATUS_COLOR_MAP[status];
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
