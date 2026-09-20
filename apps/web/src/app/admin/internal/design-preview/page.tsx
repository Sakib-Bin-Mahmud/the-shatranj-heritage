"use client";

import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";

type DemoOrder = { id: string; number: string; status: string; total: string };

const DEMO_ORDERS: DemoOrder[] = [
  { id: "1", number: "ORD-1001", status: "confirmed", total: "5200.00" },
  { id: "2", number: "ORD-1002", status: "shipped", total: "1800.00" },
];

const columns: TableColumn<DemoOrder>[] = [
  { key: "number", header: "Order #", sortable: true, render: (r) => r.number },
  {
    key: "status",
    header: "Status",
    render: (r) => (
      <Badge tone={r.status === "shipped" ? "info" : "success"}>
        {r.status}
      </Badge>
    ),
  },
  {
    key: "total",
    header: "Total",
    sortable: true,
    render: (r) => `৳${r.total}`,
  },
];

// Throwaway route exercising the F0 design-system primitives against
// the Admin layout shell. Deleted (or admin-gated) before F9's launch
// QA per docs/Frontend Implementation Plan.md Phase F0.
export default function AdminDesignPreviewPage() {
  const [page, setPage] = useState(1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <h1>Design Preview — Admin shell</h1>

      <Card title="Buttons">
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Button variant="primary">Save</Button>
          <Button variant="secondary">Cancel</Button>
          <Button variant="danger">Deactivate</Button>
        </div>
      </Card>

      <Card title="Filter bar">
        <TextField label="Search orders" placeholder="ORD-1001" />
      </Card>

      <Card title="Alerts">
        <Alert tone="danger">Refund request needs approval.</Alert>
      </Card>

      <Card title="Orders table">
        <Table
          columns={columns}
          rows={DEMO_ORDERS}
          rowKey={(r) => r.id}
          pagination={{ page, totalPages: 4, onPageChange: setPage }}
        />
      </Card>

      <Card title="Empty state">
        <EmptyState
          title="No orders match this filter"
          description="Clear filters to see all orders."
        />
      </Card>
    </div>
  );
}
