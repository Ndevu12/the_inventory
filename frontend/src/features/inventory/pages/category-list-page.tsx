"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Plus, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from "../hooks/use-categories";
import { CategoryTree } from "../components/categories/category-tree";
import { CategoryFormDialog } from "../components/categories/category-form-dialog";
import type { Category } from "../types/inventory.types";
import type { CategoryFormValues } from "../helpers/category-schemas";
import type { ApiError } from "@/types";

export function CategoryListPage() {
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Category | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);

  const { data, isLoading } = useCategories({
    search: search || undefined,
    page_size: 100,
  });
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();

  function openCreateDialog() {
    setEditTarget(null);
    setFormOpen(true);
  }

  function openEditDialog(category: Category) {
    setEditTarget(category);
    setFormOpen(true);
  }

  function closeFormDialog(open: boolean) {
    setFormOpen(open);
    if (!open) setEditTarget(null);
  }

  async function handleFormSubmit(values: CategoryFormValues) {
    try {
      if (editTarget) {
        await updateMutation.mutateAsync({ id: editTarget.id, data: values });
        toast.success(`Category "${values.name}" updated`);
      } else {
        await createMutation.mutateAsync(values);
        toast.success(`Category "${values.name}" created`);
      }
      setFormOpen(false);
      setEditTarget(null);
    } catch (err) {
      const apiErr = err as ApiError;
      toast.error(apiErr?.message || "Failed to save category");
    }
  }

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast.success(`Category "${deleteTarget.name}" deleted`);
      setDeleteTarget(null);
    } catch (err) {
      const apiErr = err as ApiError;
      toast.error(apiErr?.message || "Failed to delete category");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Categories"
        description="Organize your products into categories."
        actions={
          <Button onClick={openCreateDialog}>
            <Plus className="size-4" data-icon="inline-start" />
            Add Category
          </Button>
        }
      />

      <div className="flex items-center gap-4">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search categories…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : (
        <CategoryTree
          categories={data?.results ?? []}
          onEdit={openEditDialog}
          onDelete={setDeleteTarget}
        />
      )}

      <CategoryFormDialog
        open={formOpen}
        onOpenChange={closeFormDialog}
        category={editTarget}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete confirmation dialog */}
      <Dialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Category</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.name}
              &rdquo;? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
