import type { Metadata } from "next";
import { HomeContent } from "./home-content";

const description =
  "Handcrafted chess sets, carved by master artisans and bound in stories older than the game itself — Bangladesh's first dedicated home for the noble game.";

// The page itself has no server data (GrandCollection fetches
// client-side), but MarketingFooter's legal-page links are server-fetched
// CMS content — revalidate periodically so a newly published/unpublished
// policy page doesn't wait for the next full rebuild to show up.
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "The Shatranj Heritage — Step Into the Enchanted Chess Hall",
  description,
  openGraph: {
    title: "The Shatranj Heritage",
    description,
    type: "website",
    siteName: "The Shatranj Heritage",
  },
  twitter: {
    card: "summary_large_image",
    title: "The Shatranj Heritage",
    description,
  },
};

export default function Home() {
  return <HomeContent />;
}
