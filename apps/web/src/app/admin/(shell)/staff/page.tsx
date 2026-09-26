"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminListRoles,
  adminListStaff,
  type StaffSummary,
} from "@/lib/api/staff";
import { titleCase } from "@/lib/text-format";
import {
  Badge,
  type BadgeTone,
  Button,
  Table,
  type TableColumn,
} from "@/components/ui";
import { CreateStaffModal } from "./create-staff-modal";
import { AssignRolesModal } from "./assign-roles-modal";
import styles from "./page.module.css";

type Tab = "staff" | "roles";
const PAGE_SIZE = 20;

function staffStatusTone(status: string): BadgeTone {
  if (status === "active") return "success";
  if (status === "suspended") return "danger";
  return "neutral";
}

export default function AdminStaffPage() {
  const { accessToken } = useAdminAuth();
  const [tab, setTab] = useState<Tab>("staff");
  const [page, setPage] = useState(1);
  const [creating, setCreating] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffSummary | null>(null);

  const { data: roles } = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => adminListRoles(accessToken),
  });

  const { data: staffPage, isLoading } = useQuery({
    queryKey: ["admin-staff", page],
    queryFn: () => adminListStaff({ page, limit: PAGE_SIZE }, accessToken),
  });

  const columns: TableColumn<StaffSummary>[] = [
    { key: "full_name", header: "Name", render: (s) => s.full_name },
    { key: "email", header: "Email", render: (s) => s.email },
    {
      key: "roles",
      header: "Roles",
      render: (s) => (
        <div className={styles.roleBadges}>
          {s.roles.length > 0
            ? s.roles.map((r) => (
                <Badge key={r} tone="info">
                  {titleCase(r)}
                </Badge>
              ))
            : "—"}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (s) => (
        <Badge tone={staffStatusTone(s.status)}>{titleCase(s.status)}</Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (s) => (
        <Button variant="secondary" onClick={() => setEditingStaff(s)}>
          Edit roles
        </Button>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.headingRow}>
        <h1>Staff & Roles</h1>
        {tab === "staff" && (
          <Button onClick={() => setCreating(true)}>New staff member</Button>
        )}
      </div>

      <nav className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${tab === "staff" ? styles.tabActive : ""}`}
          onClick={() => setTab("staff")}
        >
          Staff
        </button>
        <button
          type="button"
          className={`${styles.tab} ${tab === "roles" ? styles.tabActive : ""}`}
          onClick={() => setTab("roles")}
        >
          Roles & Permissions
        </button>
      </nav>

      {tab === "staff" ? (
        <Table
          columns={columns}
          rows={staffPage?.items ?? []}
          rowKey={(s) => s.id}
          isLoading={isLoading}
          emptyTitle="No staff members yet"
          pagination={
            staffPage?.meta
              ? {
                  page: staffPage.meta.page,
                  totalPages: staffPage.meta.total_pages,
                  onPageChange: setPage,
                }
              : undefined
          }
        />
      ) : (
        <div className={styles.rolesGrid}>
          {(roles ?? []).map((role) => (
            <div key={role.id} className={styles.roleCard}>
              <span className={styles.roleName}>{titleCase(role.name)}</span>
              {role.description && (
                <span className={styles.roleDescription}>
                  {role.description}
                </span>
              )}
              <div className={styles.roleBadges}>
                {role.permissions.length > 0 ? (
                  role.permissions.map((p) => (
                    <Badge key={p} tone="neutral">
                      {p}
                    </Badge>
                  ))
                ) : (
                  <span className={styles.roleDescription}>
                    No permissions granted yet.
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateStaffModal
        open={creating}
        onClose={() => setCreating(false)}
        roles={roles ?? []}
      />
      <AssignRolesModal
        staff={editingStaff}
        onClose={() => setEditingStaff(null)}
        roles={roles ?? []}
      />
    </div>
  );
}
