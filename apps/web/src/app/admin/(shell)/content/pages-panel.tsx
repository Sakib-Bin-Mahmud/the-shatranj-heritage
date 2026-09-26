"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminCreateContentPage,
  adminGetContentPage,
  adminListContentPages,
  adminUpdateContentPage,
  type PageInput,
  type PageSummary,
} from "@/lib/api/content";
import { slugify } from "@/lib/slugify";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Badge,
  Button,
  CheckboxField,
  Modal,
  SelectField,
  Skeleton,
  Table,
  TextareaField,
  TextField,
  type TableColumn,
} from "@/components/ui";
import styles from "./page.module.css";

type PageFormValues = PageInput;

const EMPTY_INPUT: PageFormValues = {
  slug: "",
  title: "",
  body: "",
  page_type: "policy",
  is_published: false,
};

export function PagesPanel({ accessToken }: { accessToken: string | null }) {
  const queryClient = useQueryClient();
  const { data: pages, isLoading } = useQuery({
    queryKey: ["admin-content-pages"],
    queryFn: () => adminListContentPages(accessToken),
  });

  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<PageFormValues>(EMPTY_INPUT);
  const [slugTouched, setSlugTouched] = useState(false);
  const [loadingBody, setLoadingBody] = useState(false);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-content-pages"] });
  }

  function openCreate() {
    setForm(EMPTY_INPUT);
    setSlugTouched(false);
    setCreating(true);
  }

  async function openEdit(page: PageSummary) {
    setEditingId(page.id);
    setLoadingBody(true);
    try {
      const detail = await adminGetContentPage(page.id, accessToken);
      setForm({
        slug: detail.slug,
        title: detail.title,
        body: detail.body,
        page_type: detail.page_type as PageFormValues["page_type"],
        is_published: detail.is_published,
      });
    } finally {
      setLoadingBody(false);
    }
  }

  function close() {
    setCreating(false);
    setEditingId(null);
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      editingId
        ? adminUpdateContentPage(
            editingId,
            {
              title: form.title,
              body: form.body,
              page_type: form.page_type,
              is_published: form.is_published,
            },
            accessToken,
          )
        : adminCreateContentPage(form, accessToken),
    onSuccess: () => {
      invalidate();
      close();
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (page: PageSummary) =>
      adminUpdateContentPage(
        page.id,
        { is_published: !page.is_published },
        accessToken,
      ),
    onSuccess: () => invalidate(),
  });

  const columns: TableColumn<PageSummary>[] = [
    { key: "title", header: "Title", render: (p) => p.title },
    { key: "slug", header: "Slug", render: (p) => p.slug },
    { key: "page_type", header: "Type", render: (p) => p.page_type },
    {
      key: "is_published",
      header: "Status",
      render: (p) => (
        <Badge tone={p.is_published ? "success" : "neutral"}>
          {p.is_published ? "Published" : "Draft"}
        </Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (p) => (
        <div className={styles.rowActions}>
          <Button variant="secondary" size="sm" onClick={() => openEdit(p)}>
            Edit
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => toggleMutation.mutate(p)}
            disabled={toggleMutation.isPending}
          >
            {p.is_published ? "Unpublish" : "Publish"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className={styles.section}>
      <div className={styles.headingRow}>
        <h2>Pages</h2>
        <Button onClick={openCreate}>New page</Button>
      </div>

      {isLoading ? (
        <Skeleton height="10rem" />
      ) : (
        <Table
          columns={columns}
          rows={pages ?? []}
          rowKey={(p) => p.id}
          emptyTitle="No pages yet"
        />
      )}

      <Modal
        open={creating || Boolean(editingId)}
        onClose={close}
        title={editingId ? "Edit page" : "New page"}
      >
        {loadingBody ? (
          <Skeleton height="10rem" />
        ) : (
          <form
            className={styles.modalForm}
            onSubmit={(e) => {
              e.preventDefault();
              saveMutation.mutate();
            }}
          >
            <TextField
              label="Title"
              required
              value={form.title}
              onChange={(e) => {
                const title = e.target.value;
                setForm((prev) => ({
                  ...prev,
                  title,
                  slug: slugTouched ? prev.slug : slugify(title),
                }));
              }}
            />
            <TextField
              label="Slug"
              required
              disabled={Boolean(editingId)}
              value={form.slug}
              onChange={(e) => {
                setSlugTouched(true);
                setForm({ ...form, slug: e.target.value });
              }}
              hint={
                editingId ? "Slug can't be changed after creation." : undefined
              }
            />
            <SelectField
              label="Type"
              value={form.page_type}
              onChange={(e) =>
                setForm({
                  ...form,
                  page_type: e.target.value as PageFormValues["page_type"],
                })
              }
            >
              <option value="policy">Policy</option>
              <option value="page">Page</option>
              <option value="faq">FAQ</option>
            </SelectField>
            <TextareaField
              label="Body"
              required
              rows={10}
              value={form.body}
              onChange={(e) => setForm({ ...form, body: e.target.value })}
            />
            <CheckboxField
              label="Published"
              checked={form.is_published ?? false}
              onChange={(e) =>
                setForm({ ...form, is_published: e.target.checked })
              }
            />
            {saveMutation.isError && (
              <Alert tone="danger">
                {saveMutation.error instanceof ApiClientError
                  ? saveMutation.error.message
                  : "Could not save this page."}
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
        )}
      </Modal>
    </div>
  );
}
