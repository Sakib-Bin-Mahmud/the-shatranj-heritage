import { listContentPages } from "@/lib/api/content";
import { MarketingFooterContent } from "./marketing-footer-content";

// Server component: only responsible for the CMS fetch. All display
// strings (including locale-dependent ones) live in the client
// component below, which reads the real client-side locale via
// useDictionary() instead of always rendering English.
export async function MarketingFooter() {
  // Best-effort: the footer shouldn't break the whole page if the API
  // happens to be unreachable when this server component renders.
  const legalPages = await listContentPages().catch(() => []);

  return <MarketingFooterContent legalPages={legalPages} />;
}
