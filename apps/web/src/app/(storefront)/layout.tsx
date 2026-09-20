import { Suspense, type ReactNode } from "react";
import { StorefrontNav } from "@/components/storefront-nav";

export default function StorefrontLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <>
      <Suspense fallback={null}>
        <StorefrontNav />
      </Suspense>
      {children}
    </>
  );
}
