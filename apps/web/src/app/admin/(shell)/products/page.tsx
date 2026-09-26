"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListProducts, type ProductDetail } from "@/lib/api/catalog";
import {
  Badge,
  type BadgeTone,
  Button,
  SelectField,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";
import { ArtisansPanel } from "./artisans-panel";
import styles from "./page.module.css";

type Tab = "products" | "artisans";
type StatusFilter = "" | "draft" | "active" | "archived";
const PAGE_SIZE = 20;

function statusTone(status: string): BadgeTone {
  if (status === "active") return "success";
  if (status === "archived") return "danger";
  return "neutral";
}

export default function AdminProductsPage() {
  const { accessToken } = useAdminAuth();
  const [tab, setTab] = useState<Tab>("products");
  const [status, setStatus] = useState<StatusFilter>("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-products", status, search, page],
    queryFn: () =>
      adminListProducts(
        {
          status: status || undefined,
          search: search || undefined,
          page,
          limit: PAGE_SIZE,
        },
        accessToken,
      ),
  });

  const columns: TableColumn<ProductDetail>[] = [
    {
      key: "name",
      header: "Product",
      render: (p) => <Link href={`/admin/products/${p.id}`}>{p.name}</Link>,
    },
    { key: "sku", header: "SKU", render: (p) => p.sku },
    { key: "category", header: "Category", render: (p) => p.category.name },
    { key: "base_price", header: "Price", render: (p) => `৳${p.base_price}` },
    {
      key: "status",
      header: "Status",
      render: (p) => <Badge tone={statusTone(p.status)}>{p.status}</Badge>,
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.headingRow}>
        <h1>Products</h1>
        {tab === "products" && (
          <Link href="/admin/products/new">
            <Button>New product</Button>
          </Link>
        )}
      </div>

      <nav className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${tab === "products" ? styles.tabActive : ""}`}
          onClick={() => setTab("products")}
        >
          Products
        </button>
        <button
          type="button"
          className={`${styles.tab} ${tab === "artisans" ? styles.tabActive : ""}`}
          onClick={() => setTab("artisans")}
        >
          Artisans
        </button>
      </nav>

      {tab === "products" ? (
        <>
          <div className={styles.filters}>
            <TextField
              label="Search"
              placeholder="Name or SKU"
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
                setStatus(e.target.value as StatusFilter);
                setPage(1);
              }}
            >
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </SelectField>
          </div>

          <Table
            columns={columns}
            rows={data?.items ?? []}
            rowKey={(p) => p.id}
            isLoading={isLoading}
            emptyTitle="No products yet"
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
        </>
      ) : (
        <ArtisansPanel accessToken={accessToken} />
      )}
    </div>
  );
}
