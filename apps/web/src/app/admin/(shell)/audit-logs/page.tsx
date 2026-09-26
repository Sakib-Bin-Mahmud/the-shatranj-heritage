"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListAuditLogs, type AuditLogEntry } from "@/lib/api/audit";
import { titleCase } from "@/lib/text-format";
import { Button, SelectField, Table, type TableColumn } from "@/components/ui";
import { AuditDetailModal } from "./detail-modal";
import styles from "./page.module.css";

const PAGE_SIZE = 20;
const ENTITY_TYPES = [
  "admin_user",
  "customer",
  "order",
  "shipment",
  "shipping_rate",
];

export default function AdminAuditLogsPage() {
  const { accessToken } = useAdminAuth();
  const [entityType, setEntityType] = useState("");
  const [page, setPage] = useState(1);
  const [viewing, setViewing] = useState<AuditLogEntry | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-audit-logs", entityType, page],
    queryFn: () =>
      adminListAuditLogs(
        { entity_type: entityType || undefined, page, limit: PAGE_SIZE },
        accessToken,
      ),
  });

  const columns: TableColumn<AuditLogEntry>[] = [
    {
      key: "created_at",
      header: "When",
      render: (e) => new Date(e.created_at).toLocaleString(),
    },
    {
      key: "actor",
      header: "Actor",
      render: (e) => titleCase(e.actor_type),
    },
    { key: "action", header: "Action", render: (e) => e.action },
    {
      key: "entity",
      header: "Entity",
      render: (e) => (
        <div className={styles.entityCell}>
          <span>{titleCase(e.entity_type)}</span>
          <span className={styles.entityId}>{e.entity_id}</span>
        </div>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (e) => (
        <Button variant="secondary" onClick={() => setViewing(e)}>
          View details
        </Button>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <h1>Audit Log</h1>

      <div className={styles.filters}>
        <SelectField
          label="Entity type"
          value={entityType}
          onChange={(e) => {
            setEntityType(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All</option>
          {ENTITY_TYPES.map((type) => (
            <option key={type} value={type}>
              {titleCase(type)}
            </option>
          ))}
        </SelectField>
      </div>

      <Table
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(e) => e.id}
        isLoading={isLoading}
        emptyTitle="No audit log entries found"
        pagination={
          data?.meta
            ? {
                page: data.meta.page,
                totalPages: data.meta.total_pages,
                onPageChange: setPage,
              }
            : undefined
        }
      />

      <AuditDetailModal entry={viewing} onClose={() => setViewing(null)} />
    </div>
  );
}
