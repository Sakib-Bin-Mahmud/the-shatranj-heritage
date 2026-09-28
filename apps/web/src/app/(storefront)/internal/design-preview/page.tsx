"use client";

import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  CheckboxField,
  EmptyState,
  Modal,
  Pagination,
  SelectField,
  Skeleton,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";

type DemoRow = { id: string; name: string; status: string; price: string };

const DEMO_ROWS: DemoRow[] = [
  {
    id: "1",
    name: "Staunton Rosewood Set",
    status: "active",
    price: "4500.00",
  },
  { id: "2", name: "Travel Magnetic Set", status: "draft", price: "1200.00" },
];

const columns: TableColumn<DemoRow>[] = [
  { key: "name", header: "Product", sortable: true, render: (r) => r.name },
  {
    key: "status",
    header: "Status",
    render: (r) => (
      <Badge tone={r.status === "active" ? "success" : "neutral"}>
        {r.status}
      </Badge>
    ),
  },
  {
    key: "price",
    header: "Price",
    sortable: true,
    render: (r) => `৳${r.price}`,
  },
];

// Throwaway route exercising the F0 design-system primitives against
// the Storefront layout shell. Deleted (or admin-gated) before F9's
// launch QA per docs/Frontend Implementation Plan.md Phase F0.
export default function StorefrontDesignPreviewPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [page, setPage] = useState(1);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "2rem",
        padding: "2rem",
      }}
    >
      <h1>Design Preview — Storefront shell</h1>

      <Card title="Buttons">
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="primary" disabled>
            Disabled
          </Button>
        </div>
      </Card>

      <Card title="Form fields">
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
            maxWidth: 320,
          }}
        >
          <TextField label="Search products" placeholder="Staunton set…" />
          <SelectField label="Sort by">
            <option value="relevance">Relevance</option>
            <option value="price_asc">Price: low to high</option>
          </SelectField>
          <CheckboxField label="In stock only" />
        </div>
      </Card>

      <Card title="Alerts">
        <div
          style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}
        >
          <Alert tone="info">Shipping estimates update at checkout.</Alert>
          <Alert tone="success">Address saved.</Alert>
          <Alert tone="warning">Only 2 left in stock.</Alert>
          <Alert tone="danger">Could not reach the server.</Alert>
        </div>
      </Card>

      <Card title="Skeleton">
        <Skeleton width={240} height={20} />
      </Card>

      <Card title="Empty state">
        <EmptyState
          title="No results"
          description="Try a different search term or filter."
        />
      </Card>

      <Card title="Table (sortable + paginated)">
        <Table
          columns={columns}
          rows={DEMO_ROWS}
          rowKey={(r) => r.id}
          pagination={{ page, totalPages: 3, onPageChange: setPage }}
        />
      </Card>

      <Card title="Pagination (standalone)">
        <Pagination page={page} totalPages={3} onPageChange={setPage} />
      </Card>

      <Card title="Modal">
        <Button onClick={() => setModalOpen(true)}>Open modal</Button>
        <Modal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Confirm action"
        >
          <p>This is the shared Modal primitive.</p>
          <Button onClick={() => setModalOpen(false)}>Close</Button>
        </Modal>
      </Card>
    </div>
  );
}
