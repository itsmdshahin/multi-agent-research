import type { Metadata } from "next";
import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";

export const metadata: Metadata = {
  title: "ResearchAI — Multi-Agent Research Assistant",
  description: "Enterprise AI research platform with multi-agent orchestration, PDF ingestion, RAG, and intelligent synthesis.",
  keywords: ["AI", "research", "RAG", "PDF", "LangGraph", "multi-agent"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-background antialiased">
        {children}
        <ToastProvider />
      </body>
    </html>
  );
}
