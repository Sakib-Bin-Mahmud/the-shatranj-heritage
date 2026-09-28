import { Suspense, type ReactNode } from "react";
import { StorefrontNav } from "@/components/storefront-nav";

export default function StorefrontLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Suspense fallback={null}>
        <StorefrontNav />
      </Suspense>
      <main id="main">{children}</main>
    </>
  );
}
