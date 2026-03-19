"use client";

import { useState } from "react";
import {
  ChevronRightIcon,
  PencilIcon,
  Trash2Icon,
  WarehouseIcon,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CapacityBar } from "./capacity-bar";
import { useLocationStock, useDeleteLocation } from "../../hooks/use-locations";
import type { StockLocation, StockRecordAtLocation } from "../../types/location.types";

/* ------------------------------------------------------------------ */
/*  Stock-records sub-table (lazy-loaded when a node is expanded)     */
/* ------------------------------------------------------------------ */

function StockRecordsPanel({ locationId }: { locationId: number }) {
  const { data: records, isLoading } = useLocationStock(locationId);

  if (isLoading) {
    return (
      <div className="space-y-2 px-4 py-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-full" />
        ))}
      </div>
    );
  }

  if (!records?.length) {
    return (
      <p className="px-4 py-4 text-center text-sm text-muted-foreground">
        No stock at this location.
      </p>
    );
  }

  return (
    <div className="border-t">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50 text-left">
            <th className="px-4 py-2 font-medium">Product</th>
            <th className="px-4 py-2 text-right font-medium">Qty</th>
            <th className="px-4 py-2 text-right font-medium">Reserved</th>
            <th className="px-4 py-2 text-right font-medium">Available</th>
          </tr>
        </thead>
        <tbody>
          {(records as StockRecordAtLocation[]).map((r) => (
            <tr key={r.id} className="border-b last:border-0">
              <td className="px-4 py-2">
                <div className="font-medium">{r.product_name}</div>
                <div className="text-xs text-muted-foreground">
                  {r.product_sku}
                </div>
              </td>
              <td className="px-4 py-2 text-right tabular-nums">
                {r.quantity}
              </td>
              <td className="px-4 py-2 text-right tabular-nums">
                {r.reserved_quantity}
              </td>
              <td className="px-4 py-2 text-right tabular-nums">
                <span
                  className={cn(
                    r.is_low_stock && "font-medium text-destructive",
                  )}
                >
                  {r.available_quantity}
                </span>
                {r.is_low_stock && (
                  <Badge variant="destructive" className="ml-2 text-[10px]">
                    Low
                  </Badge>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Single location row                                               */
/* ------------------------------------------------------------------ */

interface LocationItemProps {
  location: StockLocation;
  onEdit: (location: StockLocation) => void;
}

function LocationItem({ location, onEdit }: LocationItemProps) {
  const [expanded, setExpanded] = useState(false);
  const deleteMutation = useDeleteLocation();

  const handleDelete = () => {
    if (!confirm(`Delete "${location.name}"? This cannot be undone.`))
      return;

    deleteMutation.mutate(location.id, {
      onSuccess: () => toast.success(`"${location.name}" deleted`),
      onError: (err) =>
        toast.error(err.message || "Failed to delete location"),
    });
  };

  return (
    <div className="overflow-hidden rounded-lg border bg-card transition-shadow hover:shadow-sm">
      <div className="flex items-center gap-3 p-4">
        {/* expand / collapse */}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setExpanded((v) => !v)}
          aria-label={expanded ? "Collapse" : "Expand"}
        >
          <ChevronRightIcon
            className={cn(
              "size-4 transition-transform duration-200",
              expanded && "rotate-90",
            )}
          />
        </Button>

        {/* info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate font-medium">{location.name}</span>
            <Badge
              variant={location.is_active ? "default" : "secondary"}
              className="shrink-0"
            >
              {location.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
          {location.description && (
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {location.description}
            </p>
          )}
        </div>

        {/* capacity (hidden on mobile, shown inline on sm+) */}
        <div className="hidden w-48 shrink-0 sm:block">
          <CapacityBar
            currentUtilization={location.current_utilization}
            maxCapacity={location.max_capacity}
          />
        </div>

        {/* actions */}
        <div className="flex shrink-0 items-center gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => onEdit(location)}
            aria-label="Edit location"
          >
            <PencilIcon className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            aria-label="Delete location"
          >
            <Trash2Icon className="size-4" />
          </Button>
        </div>
      </div>

      {/* mobile capacity bar */}
      <div className="px-4 pb-3 sm:hidden">
        <CapacityBar
          currentUtilization={location.current_utilization}
          maxCapacity={location.max_capacity}
        />
      </div>

      {/* expandable stock records */}
      {expanded && <StockRecordsPanel locationId={location.id} />}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Tree / list wrapper                                               */
/* ------------------------------------------------------------------ */

interface LocationTreeProps {
  locations: StockLocation[];
  onEdit: (location: StockLocation) => void;
  isLoading?: boolean;
}

export function LocationTree({
  locations,
  onEdit,
  isLoading,
}: LocationTreeProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[72px] w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!locations.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
        <WarehouseIcon className="mb-4 size-12 text-muted-foreground/50" />
        <h3 className="text-lg font-medium">No locations yet</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Create your first stock location to start tracking inventory.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {locations.map((loc) => (
        <LocationItem key={loc.id} location={loc} onEdit={onEdit} />
      ))}
    </div>
  );
}
