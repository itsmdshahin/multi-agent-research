"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { useChatStore } from "@/lib/stores/chatStore";
import { Sidebar } from "@/components/layout/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, fetchMe } = useAuthStore();
  const { loadConversations } = useChatStore();

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().isAuthenticated) {
        router.push("/auth/login");
      } else {
        loadConversations();
      }
    });
  }, []);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto" style={{ marginLeft: "var(--sidebar-width)" }}>
        {children}
      </main>
    </div>
  );
}
