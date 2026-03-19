"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ExpiryBadgeProps {
  daysToExpiry: number | null;
  isExpired: boolean;
  className?: string;
}

function getExpiryConfig(daysToExpiry: number | null, isExpired: boolean) {
  if (isExpired || (daysToExpiry !== null && daysToExpiry <= 0)) {
    return {
      label: "Expired",
      className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    };
  }

  if (daysToExpiry === null) {
    return {
      label: "No expiry",
      className:
        "bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400",
    };
  }

  if (daysToExpiry <= 30) {
    return {
      label: `${daysToExpiry}d left`,
      className:
        "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    };
  }

  if (daysToExpiry <= 90) {
    return {
      label: `${daysToExpiry}d left`,
      className:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    };
  }

  return {
    label: `${daysToExpiry}d left`,
    className:
      "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  };
}

export function ExpiryBadge({
  daysToExpiry,
  isExpired,
  className,
}: ExpiryBadgeProps) {
  const config = getExpiryConfig(daysToExpiry, isExpired);

  return (
    <Badge
      variant="outline"
      className={cn("border-transparent font-medium", config.className, className)}
    >
      {config.label}
    </Badge>
  );
}
