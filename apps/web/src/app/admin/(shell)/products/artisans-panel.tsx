"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminCreateArtisan,
  adminListArtisans,
  adminUpdateArtisan,
  type Artisan,
  type ArtisanInput,
} from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Button,
  Modal,
  Skeleton,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";
import styles from "./page.module.css";

const EMPTY_INPUT: ArtisanInput = {
  name: "",
  region: "",
  bio: "",
  photo_url: "",
};

export function ArtisansPanel({ accessToken }: { accessToken: string | null }) {
  const queryClient = useQueryClient();
  const { data: artisans, isLoading } = useQuery({
    queryKey: ["admin-artisans"],
    queryFn: () => adminListArtisans(accessToken),
  });

  const [editing, setEditing] = useState<Artisan | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<ArtisanInput>(EMPTY_INPUT);

  function openCreate() {
    setForm(EMPTY_INPUT);
    setCreating(true);
  }

  function openEdit(artisan: Artisan) {
    setForm({
      name: artisan.name,
      region: artisan.region ?? "",
      bio: artisan.bio ?? "",
      photo_url: artisan.photo_url ?? "",
    });
    setEditing(artisan);
  }

  function close() {
    setCreating(false);
    setEditing(null);
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const input: ArtisanInput = {
        name: form.name,
        region: form.region || null,
        bio: form.bio || null,
        photo_url: form.photo_url || null,
      };
      return editing
        ? adminUpdateArtisan(editing.id, input, accessToken)
        : adminCreateArtisan(input, accessToken);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-artisans"] });
      close();
    },
  });

  const columns: TableColumn<Artisan>[] = [
    { key: "name", header: "Name", render: (a) => a.name },
    { key: "region", header: "Region", render: (a) => a.region ?? "—" },
    {
      key: "actions",
      header: "",
      render: (a) => (
        <Button variant="secondary" size="sm" onClick={() => openEdit(a)}>
          Edit
        </Button>
      ),
    },
  ];

  return (
    <div className={styles.section}>
      <div className={styles.headingRow}>
        <h2>Artisans</h2>
        <Button onClick={openCreate}>New artisan</Button>
      </div>

      {isLoading ? (
        <Skeleton height="10rem" />
      ) : (
        <Table
          columns={columns}
          rows={artisans ?? []}
          rowKey={(a) => a.id}
          emptyTitle="No artisans yet"
        />
      )}

      <Modal
        open={creating || Boolean(editing)}
        onClose={close}
        title={editing ? "Edit artisan" : "New artisan"}
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
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            label="Region"
            value={form.region ?? ""}
            onChange={(e) => setForm({ ...form, region: e.target.value })}
          />
          <TextField
            label="Bio"
            value={form.bio ?? ""}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
          />
          <TextField
            label="Photo URL"
            value={form.photo_url ?? ""}
            onChange={(e) => setForm({ ...form, photo_url: e.target.value })}
          />
          {saveMutation.isError && (
            <Alert tone="danger">
              {saveMutation.error instanceof ApiClientError
                ? saveMutation.error.message
                : "Could not save this artisan."}
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
