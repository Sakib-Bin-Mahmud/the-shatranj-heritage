"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListCustomers, type CustomerProfile } from "@/lib/api/customers";
import { titleCase } from "@/lib/text-format";
import {
  Badge,
  type BadgeTone,
  SelectField,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";
import styles from "./page.module.css";

const PAGE_SIZE = 20;

function customerStatusTone(status: string): BadgeTone {
  if (status === "active") return "success";
  if (status === "suspended") return "danger";
  return "neutral";
}

export default function AdminCustomersPage() {
  const { accessToken } = useAdminAuth();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-customers", search, status, page],
    queryFn: () =>
      adminListCustomers(
        {
          search: search || undefined,
          status: (status || undefined) as
            "active" | "inactive" | "suspended" | undefined,
          page,
          limit: PAGE_SIZE,
        },
        accessToken,
      ),
  });

  const columns: TableColumn<CustomerProfile>[] = [
    {
      key: "full_name",
      header: "Name",
      render: (c) => (
        <Link href={`/admin/customers/${c.id}`}>{c.full_name}</Link>
      ),
    },
    {
      key: "contact",
      header: "Contact",
      render: (c) => c.email ?? c.mobile_number ?? "—",
    },
    {
      key: "preferred_language",
      header: "Language",
      render: (c) => (c.preferred_language === "bn" ? "Bangla" : "English"),
    },
    {
      key: "status",
      header: "Status",
      render: (c) => (
        <Badge tone={customerStatusTone(c.status)}>{titleCase(c.status)}</Badge>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <h1>Customers</h1>

      <div className={styles.filters}>
        <TextField
          label="Search"
          placeholder="Name, email, or phone"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <SelectField
          label="Status"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="suspended">Suspended</option>
        </SelectField>
      </div>

      <Table
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(c) => c.id}
        isLoading={isLoading}
        emptyTitle="No customers found"
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
    </div>
  );
}
