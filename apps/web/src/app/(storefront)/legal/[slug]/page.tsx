import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getContentPage } from "@/lib/api/content";
import { ApiClientError } from "@/lib/api-client";
import styles from "./page.module.css";

type Params = { slug: string };

// Live CMS content — never prerender against build-time API state.
export const dynamic = "force-dynamic";

async function loadPage(slug: string) {
  try {
    return await getContentPage(slug);
  } catch (error) {
    if (error instanceof ApiClientError && error.code === "NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const page = await loadPage(slug);
  if (!page) return {};
  return { title: `${page.title} — The Shatranj Heritage` };
}

export default async function LegalPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { slug } = await params;
  const page = await loadPage(slug);
  if (!page) notFound();

  return (
    <div className={styles.page}>
      <h1>{page.title}</h1>
      <div className={styles.body}>{page.body}</div>
    </div>
  );
}
