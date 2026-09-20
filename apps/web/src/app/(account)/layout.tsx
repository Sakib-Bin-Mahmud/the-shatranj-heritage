import type { ReactNode } from "react";
import { NavBar } from "@/components/nav-bar";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <NavBar />
      {children}
    </>
  );
}
