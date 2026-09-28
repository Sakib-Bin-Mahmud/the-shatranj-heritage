"use client";

import { usePageTitle } from "@/lib/use-page-title";
import { useState } from "react";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { CategoriesPanel } from "./categories-panel";
import { PagesPanel } from "./pages-panel";
import styles from "./page.module.css";

type Tab = "categories" | "pages";

export default function AdminContentPage() {
  usePageTitle("Content");
  const { accessToken, hasPermission } = useAdminAuth();
  const canCategories = hasPermission("categories.write");
  const canPages = hasPermission("cms.write");
  const [tab, setTab] = useState<Tab>(canCategories ? "categories" : "pages");

  return (
    <div className={styles.page}>
      <h1>Content</h1>

      <div className={styles.tabs} role="tablist" aria-label="Content sections">
        {canCategories && (
          <button
            type="button"
            role="tab"
            id="tab-categories"
            aria-selected={tab === "categories"}
            aria-controls="tabpanel-categories"
            className={`${styles.tab} ${tab === "categories" ? styles.tabActive : ""}`}
            onClick={() => setTab("categories")}
          >
            Categories
          </button>
        )}
        {canPages && (
          <button
            type="button"
            role="tab"
            id="tab-pages"
            aria-selected={tab === "pages"}
            aria-controls="tabpanel-pages"
            className={`${styles.tab} ${tab === "pages" ? styles.tabActive : ""}`}
            onClick={() => setTab("pages")}
          >
            Pages
          </button>
        )}
      </div>

      {tab === "categories" && canCategories && (
        <div
          role="tabpanel"
          id="tabpanel-categories"
          aria-labelledby="tab-categories"
          tabIndex={0}
        >
          <CategoriesPanel accessToken={accessToken} />
        </div>
      )}
      {tab === "pages" && canPages && (
        <div
          role="tabpanel"
          id="tabpanel-pages"
          aria-labelledby="tab-pages"
          tabIndex={0}
        >
          <PagesPanel accessToken={accessToken} />
        </div>
      )}
    </div>
  );
}
