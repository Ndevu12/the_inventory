import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface AuthFeatureRowProps {
  icon: LucideIcon;
  title: string;
  description: string;
  compact?: boolean;
  /** Smaller type and icon for secondary / marketing columns. */
  supporting?: boolean;
}

export function AuthFeatureRow({
  icon: Icon,
  title,
  description,
  compact,
  supporting,
}: AuthFeatureRowProps) {
  const iconMuted = compact || supporting;
  return (
    <div className={cn("flex", supporting ? "gap-2" : "gap-3")}>
      <div
        className={cn(
          "flex shrink-0 items-center justify-center rounded-full bg-muted",
          supporting ? "size-7" : "size-9",
        )}
        aria-hidden
      >
        <Icon
          className={cn(
            supporting ? "size-3.5" : "size-4",
            iconMuted ? "text-muted-foreground" : "text-primary",
          )}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "text-pretty font-medium leading-tight text-foreground",
            supporting ? "text-xs" : "text-sm",
          )}
        >
          {title}
        </p>
        <p
          className={cn(
            "text-pretty leading-snug text-muted-foreground",
            supporting ? "text-[11px] leading-snug" : compact ? "text-sm" : "text-xs",
          )}
        >
          {description}
        </p>
      </div>
    </div>
  );
}
