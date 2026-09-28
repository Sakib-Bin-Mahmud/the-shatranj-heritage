"use client";

import Link from "next/link";
import { useDictionary } from "@/i18n/dictionary-context";
import type { PageSummary } from "@/lib/api/content";
import { EmptyState } from "@/components/ui";
import styles from "./page.module.css";

export function LegalIndexContent({ pages }: { pages: PageSummary[] }) {
  const { dict } = useDictionary();

  return (
    <div className={styles.page}>
      <h1>{dict.legal.heading}</h1>
      {pages.length === 0 ? (
        <EmptyState title={dict.legal.empty} />
      ) : (
        <ul className={styles.list}>
          {pages.map((page) => (
            <li key={page.slug}>
              <Link href={`/legal/${page.slug}`}>{page.title}</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
