import { cn } from "@/lib/utils";

interface CapacityBarProps {
  currentUtilization: number;
  maxCapacity: number | null;
  className?: string;
}

function utilizationColor(pct: number) {
  if (pct < 50) return "bg-emerald-500";
  if (pct < 80) return "bg-amber-500";
  return "bg-red-500";
}

export function CapacityBar({
  currentUtilization,
  maxCapacity,
  className,
}: CapacityBarProps) {
  if (maxCapacity === null) {
    return (
      <div
        className={cn(
          "flex items-center gap-1.5 text-xs text-muted-foreground",
          className,
        )}
      >
        <span className="tabular-nums font-medium text-foreground">
          {currentUtilization}
        </span>
        <span>units &middot; unlimited</span>
      </div>
    );
  }

  const pct =
    maxCapacity > 0
      ? Math.min((currentUtilization / maxCapacity) * 100, 100)
      : 0;

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span className="tabular-nums">
          {currentUtilization} / {maxCapacity}
        </span>
        <span className="tabular-nums">{Math.round(pct)}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            utilizationColor(pct),
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
