import type { ReactNode } from "react";
import { StorefrontNav } from "@/components/storefront-nav";

export default function StorefrontLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <>
      <StorefrontNav />
      {children}
    </>
  );
}
