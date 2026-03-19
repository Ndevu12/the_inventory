"use client";

import { useState } from "react";
import {
  ChevronRight,
  Pencil,
  Trash2,
  FolderTree,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Category } from "../../types/inventory.types";

interface CategoryTreeProps {
  categories: Category[];
  onEdit: (category: Category) => void;
  onDelete: (category: Category) => void;
}

export function CategoryTree({
  categories,
  onEdit,
  onDelete,
}: CategoryTreeProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  function toggle(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
        <FolderTree className="mb-3 size-10 opacity-40" />
        <p className="text-sm font-medium">No categories found</p>
        <p className="mt-1 text-xs">Create a category to get started.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card">
      {categories.map((cat, idx) => {
        const isExpanded = expanded.has(cat.id);

        return (
          <div
            key={cat.id}
            className={cn(idx > 0 && "border-t")}
          >
            <div className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/50">
              <button
                type="button"
                onClick={() => toggle(cat.id)}
                className="flex size-5 shrink-0 items-center justify-center rounded-sm text-muted-foreground hover:text-foreground"
              >
                <ChevronRight
                  className={cn(
                    "size-4 transition-transform duration-150",
                    isExpanded && "rotate-90",
                  )}
                />
              </button>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium">{cat.name}</span>
                  <span className="shrink-0 font-mono text-xs text-muted-foreground">
                    {cat.slug}
                  </span>
                </div>
              </div>

              <Badge variant={cat.is_active ? "secondary" : "outline"}>
                {cat.is_active ? "Active" : "Inactive"}
              </Badge>

              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onEdit(cat)}
                  aria-label={`Edit ${cat.name}`}
                >
                  <Pencil className="size-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onDelete(cat)}
                  aria-label={`Delete ${cat.name}`}
                >
                  <Trash2 className="size-3.5 text-destructive" />
                </Button>
              </div>
            </div>

            {isExpanded && (
              <div className="border-t bg-muted/25 px-12 py-3">
                <p className="text-sm text-muted-foreground">
                  {cat.description || "No description provided."}
                </p>
                <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
                  <span>
                    Created{" "}
                    {new Date(cat.created_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                  <span>
                    Updated{" "}
                    {new Date(cat.updated_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
