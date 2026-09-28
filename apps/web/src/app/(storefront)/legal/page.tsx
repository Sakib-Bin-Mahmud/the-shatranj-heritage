import type { Metadata } from "next";
import { listContentPages } from "@/lib/api/content";
import { LegalIndexContent } from "./legal-index-content";

export const metadata: Metadata = {
  title: "Legal & Policies — The Shatranj Heritage",
  description: "Terms, privacy, shipping, returns, and warranty policies.",
};

// Live CMS content — never prerender against build-time API state.
export const dynamic = "force-dynamic";

export default async function LegalIndexPage() {
  const pages = await listContentPages();
  return <LegalIndexContent pages={pages} />;
}
