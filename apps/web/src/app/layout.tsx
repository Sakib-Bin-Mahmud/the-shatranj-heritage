import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NavBar } from "@/components/nav-bar";
import { AuthProvider } from "@/lib/auth-context";
import { DictionaryProvider } from "@/i18n/dictionary-context";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "The Shatranj Heritage",
  description: "Bangladesh's first dedicated e-commerce platform for chess.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <DictionaryProvider>
          <AuthProvider>
            <NavBar />
            {children}
          </AuthProvider>
        </DictionaryProvider>
      </body>
    </html>
  );
}
