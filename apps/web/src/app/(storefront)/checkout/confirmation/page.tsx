import type { Metadata } from "next";
import { Suspense } from "react";
import { ConfirmationContent } from "./confirmation-content";

export const metadata: Metadata = {
  title: "Order confirmation — The Shatranj Heritage",
};

export default function OrderConfirmationPage() {
  return (
    <Suspense fallback={null}>
      <ConfirmationContent />
    </Suspense>
  );
}
