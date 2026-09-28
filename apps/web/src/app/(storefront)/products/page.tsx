import type { Metadata } from "next";
import { Suspense } from "react";
import { ProductsContent } from "./products-content";

export const metadata: Metadata = {
  title: "The Collection — The Shatranj Heritage",
  description: "Browse handcrafted chess sets, boards, and collector's pieces.",
};

export default function ProductsPage() {
  return (
    <Suspense fallback={null}>
      <ProductsContent />
    </Suspense>
  );
}
