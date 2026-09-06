import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "LexGuard Dashboard — Legal Hallucination Monitor",
  description:
    "Real-time analytics and evaluation dashboard for the LexGuard legal-domain LLM hallucination detector.",
  keywords: "legal AI, hallucination detection, LLM safety, trust score",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.variable}>
        <div className="app-shell">
          <Navbar />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
