"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminCreateCategory,
  adminDeactivateCategory,
  adminListCategories,
  adminUpdateCategory,
  type Category,
  type CategoryInput,
  type CategoryTree,
} from "@/lib/api/catalog";
import { buildCategoryTree, descendantIdsOf } from "@/lib/build-category-tree";
import { slugify } from "@/lib/slugify";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Modal,
  SelectField,
  Skeleton,
  TextField,
} from "@/components/ui";
import styles from "./page.module.css";

const EMPTY_INPUT: CategoryInput = {
  name: "",
  slug: "",
  description: "",
  parent_category_id: null,
  sort_order: 0,
};

function CategoryRow({
  node,
  depth,
  onEdit,
  onToggle,
}: {
  node: CategoryTree;
  depth: number;
  onEdit: (category: Category) => void;
  onToggle: (category: Category) => void;
}) {
  return (
    <>
      <div
        className={styles.categoryRow}
        style={{ paddingLeft: `${depth * 1.5}rem` }}
      >
        <span className={styles.categoryName}>{node.name}</span>
        <span className={styles.categorySlug}>{node.slug}</span>
        <Badge tone={node.is_active ? "success" : "neutral"}>
          {node.is_active ? "Active" : "Inactive"}
        </Badge>
        <div className={styles.rowActions}>
          <Button variant="secondary" size="sm" onClick={() => onEdit(node)}>
            Edit
          </Button>
          <Button
            variant={node.is_active ? "danger" : "secondary"}
            size="sm"
            onClick={() => onToggle(node)}
          >
            {node.is_active ? "Deactivate" : "Reactivate"}
          </Button>
        </div>
      </div>
      {node.children.map((child) => (
        <CategoryRow
          key={child.id}
          node={child}
          depth={depth + 1}
          onEdit={onEdit}
          onToggle={onToggle}
        />
      ))}
    </>
  );
}

export function CategoriesPanel({
  accessToken,
}: {
  accessToken: string | null;
}) {
  const queryClient = useQueryClient();
  const { data: categories, isLoading } = useQuery({
    queryKey: ["admin-categories"],
    queryFn: () => adminListCategories(accessToken),
  });

  const tree = useMemo(
    () => (categories ? buildCategoryTree(categories) : []),
    [categories],
  );

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form, setForm] = useState<CategoryInput>(EMPTY_INPUT);
  const [slugTouched, setSlugTouched] = useState(false);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
  }

  function openCreate() {
    setForm(EMPTY_INPUT);
    setSlugTouched(false);
    setCreating(true);
  }

  function openEdit(category: Category) {
    setForm({
      name: category.name,
      slug: category.slug,
      description: category.description ?? "",
      parent_category_id: category.parent_category_id,
      sort_order: category.sort_order,
    });
    setSlugTouched(true);
    setEditing(category);
  }

  function close() {
    setCreating(false);
    setEditing(null);
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      editing
        ? adminUpdateCategory(editing.id, form, accessToken)
        : adminCreateCategory(form, accessToken),
    onSuccess: () => {
      invalidate();
      close();
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (category: Category) =>
      category.is_active
        ? adminDeactivateCategory(category.id, accessToken)
        : adminUpdateCategory(category.id, { is_active: true }, accessToken),
    onSuccess: () => invalidate(),
  });

  const excludedParentIds = editing
    ? [editing.id, ...descendantIdsOf(categories ?? [], editing.id)]
    : [];

  return (
    <div className={styles.section}>
      <div className={styles.headingRow}>
        <h2>Categories</h2>
        <Button onClick={openCreate}>New category</Button>
      </div>

      {isLoading ? (
        <Skeleton height="10rem" />
      ) : tree.length === 0 ? (
        <EmptyState title="No categories yet" />
      ) : (
        <div className={styles.categoryTree}>
          {tree.map((node) => (
            <CategoryRow
              key={node.id}
              node={node}
              depth={0}
              onEdit={openEdit}
              onToggle={(c) => toggleMutation.mutate(c)}
            />
          ))}
        </div>
      )}

      <Modal
        open={creating || Boolean(editing)}
        onClose={close}
        title={editing ? "Edit category" : "New category"}
      >
        <form
          className={styles.modalForm}
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate();
          }}
        >
          <TextField
            label="Name"
            required
            value={form.name}
            onChange={(e) => {
              const name = e.target.value;
              setForm((prev) => ({
                ...prev,
                name,
                slug: slugTouched ? prev.slug : slugify(name),
              }));
            }}
          />
          <TextField
            label="Slug"
            required
            value={form.slug}
            onChange={(e) => {
              setSlugTouched(true);
              setForm({ ...form, slug: e.target.value });
            }}
          />
          <TextField
            label="Description"
            value={form.description ?? ""}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <SelectField
            label="Parent category"
            value={form.parent_category_id ?? ""}
            onChange={(e) =>
              setForm({
                ...form,
                parent_category_id: e.target.value || null,
              })
            }
          >
            <option value="">None (top level)</option>
            {categories
              ?.filter((c) => !excludedParentIds.includes(c.id))
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
          </SelectField>
          <TextField
            label="Sort order"
            type="number"
            value={form.sort_order ?? 0}
            onChange={(e) =>
              setForm({ ...form, sort_order: Number(e.target.value) })
            }
          />
          {saveMutation.isError && (
            <Alert tone="danger">
              {saveMutation.error instanceof ApiClientError
                ? saveMutation.error.message
                : "Could not save this category."}
            </Alert>
          )}
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={close}>
              Cancel
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              Save
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
