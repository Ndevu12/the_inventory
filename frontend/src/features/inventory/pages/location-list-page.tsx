"use client";

import { useState, useDeferredValue } from "react";
import { PlusIcon, SearchIcon } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLocations } from "../hooks/use-locations";
import { LocationTree } from "../components/locations/location-tree";
import { LocationFormDialog } from "../components/locations/location-form-dialog";
import type { StockLocation } from "../types/location.types";

export function LocationListPage() {
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);

  const params: Record<string, string> = {};
  if (deferredSearch) params.search = deferredSearch;

  const { data, isLoading } = useLocations(params);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLocation, setEditingLocation] =
    useState<StockLocation | null>(null);

  const openCreate = () => {
    setEditingLocation(null);
    setDialogOpen(true);
  };

  const openEdit = (loc: StockLocation) => {
    setEditingLocation(loc);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Locations"
        description="Manage warehouse locations and track capacity utilization."
        actions={
          <Button onClick={openCreate}>
            <PlusIcon className="size-4" data-icon="inline-start" />
            Add Location
          </Button>
        }
      />

      <div className="flex items-center gap-4">
        <div className="relative max-w-sm flex-1">
          <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search locations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <LocationTree
        locations={data?.results ?? []}
        onEdit={openEdit}
        isLoading={isLoading}
      />

      <LocationFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        location={editingLocation}
      />
    </div>
  );
}
