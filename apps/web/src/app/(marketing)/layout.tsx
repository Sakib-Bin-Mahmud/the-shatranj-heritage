import type { ReactNode } from "react";
import { Cinzel, Cinzel_Decorative, EB_Garamond } from "next/font/google";
import { MarketingNav } from "@/components/marketing-nav";
import { MarketingFooter } from "@/components/marketing-footer";
import "@/styles/theme.css";

const cinzel = Cinzel({
  variable: "--font-cinzel",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
});

const cinzelDecorative = Cinzel_Decorative({
  variable: "--font-cinzel-decorative",
  subsets: ["latin"],
  weight: ["400", "700"],
});

const ebGaramond = EB_Garamond({
  variable: "--font-eb-garamond",
  subsets: ["latin"],
});

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div
      data-theme="enchanted"
      className={`${cinzel.variable} ${cinzelDecorative.variable} ${ebGaramond.variable}`}
      style={{ display: "flex", flexDirection: "column", minHeight: "100%" }}
    >
      <MarketingNav />
      {children}
      <MarketingFooter />
    </div>
  );
}
