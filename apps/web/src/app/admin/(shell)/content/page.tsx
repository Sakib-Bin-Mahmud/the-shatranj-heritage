"use client";

import { useState } from "react";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { CategoriesPanel } from "./categories-panel";
import { PagesPanel } from "./pages-panel";
import styles from "./page.module.css";

type Tab = "categories" | "pages";

export default function AdminContentPage() {
  const { accessToken, hasPermission } = useAdminAuth();
  const canCategories = hasPermission("categories.write");
  const canPages = hasPermission("cms.write");
  const [tab, setTab] = useState<Tab>(canCategories ? "categories" : "pages");

  return (
    <div className={styles.page}>
      <h1>Content</h1>

      <nav className={styles.tabs}>
        {canCategories && (
          <button
            type="button"
            className={`${styles.tab} ${tab === "categories" ? styles.tabActive : ""}`}
            onClick={() => setTab("categories")}
          >
            Categories
          </button>
        )}
        {canPages && (
          <button
            type="button"
            className={`${styles.tab} ${tab === "pages" ? styles.tabActive : ""}`}
            onClick={() => setTab("pages")}
          >
            Pages
          </button>
        )}
      </nav>

      {tab === "categories" && canCategories && (
        <CategoriesPanel accessToken={accessToken} />
      )}
      {tab === "pages" && canPages && <PagesPanel accessToken={accessToken} />}
    </div>
  );
}
