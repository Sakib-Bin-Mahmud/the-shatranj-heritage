import type { Metadata } from "next";
import Link from "next/link";
import { listContentPages } from "@/lib/api/content";
import { EmptyState } from "@/components/ui";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Legal & Policies — The Shatranj Heritage",
  description: "Terms, privacy, shipping, returns, and warranty policies.",
};

// Live CMS content — never prerender against build-time API state.
export const dynamic = "force-dynamic";

export default async function LegalIndexPage() {
  const pages = await listContentPages();

  return (
    <div className={styles.page}>
      <h1>Legal &amp; Policies</h1>
      {pages.length === 0 ? (
        <EmptyState title="No policy pages published yet" />
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
