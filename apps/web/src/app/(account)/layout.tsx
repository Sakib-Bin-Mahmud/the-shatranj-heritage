import type { ReactNode } from "react";
import { NavBar } from "@/components/nav-bar";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <NavBar />
      <main id="main">{children}</main>
    </>
  );
}
